#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : oauth.py
# @Author: Pen
# @Date  : 2018-09-19 15:27
# @Desc  : oauth授权Mixin
import base64
from datetime import timedelta

import binascii
from urllib.parse import unquote_plus

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from oauthlib.oauth2 import RequestValidator

from oauth_pen.exceptions import ErrorConfigException
from oauth_pen import models
from oauth_pen.models import get_application_model, get_user_model, ApplicationAbstract
from oauth_pen.settings import oauth_pen_settings


class OAuthValidator(RequestValidator):
    """
    按照oauth2.0的规范，验证当前请求是否需要授权
    """
    @classmethod
    def _load_application(cls, client_id, request):
        """
        初始化当前请求的客户端
        :param client_id:客户端ID
        :param request:当前请求
        :return:客户端
        """
        try:
            request.client = request.client or get_application_model().objects.get(client_id=client_id)
            if request.client.is_usable(request):
                return request.client

        except ObjectDoesNotExist:
            return None
        else:
            return None

    @classmethod
    def _basic_auth_string(cls, request):
        """
        获取 basic认证的授权token
        :param request: 请求
        :return:
        """
        auth = request.headers.get('HTTP_AUTHORIZATION', None)
        if auth:
            auth_par = auth.split(' ', 1)
            if len(auth_par) == 2 and auth_par[0] == 'Basic':
                return auth_par[1]

        return None

    @classmethod
    def _authenticate_basic_auth(cls, request):
        """
        客户端basic 认证
        :param request:
        :return:
        """
        auth_str = cls._basic_auth_string(request)
        if not auth_str:
            return False

        try:
            encoding = request.encoding or settings.DEFAULT_CHARSET or 'utf-8'
        except AttributeError:
            encoding = 'utf-8'

        try:
            b64_decoded = base64.b64decode(auth_str)
        except (TypeError, binascii.Error):
            return False

        try:
            auth_string_decoded = b64_decoded.decode(encoding)
        except UnicodeDecodeError:
            return False

        client_id, client_secret = map(unquote_plus, auth_string_decoded.split(':', 1))

        if cls._load_application(client_id, request) is None:
            return False
        elif request.client.client_id != client_id:
            return False
        elif request.client.client_secret != client_secret:
            return False
        else:
            return True

    @classmethod
    def _authenticate_request_body(cls, request):
        """
        客户端认证（通过body传参数）
        """
        try:
            client_id = request.client_id
            client_secret = request.client_secret
        except AttributeError:
            return False

        if cls._load_application(client_id, request) is None:
            return False
        elif request.client.client_secret != client_secret:
            return False
        else:
            return True

    def validate_bearer_token(self, token, scopes, request):
        """
        验证请求中的token 是否有效
        :param token: token
        :param scopes: 授权范围（不予实现）
        :param request:当前请求
        :return:
        """
        if not token:
            return False

        try:
            access_token = models.AccessToken.objects.select_related('application', 'user').get(token=token)

            if access_token.is_valid():
                request.client = access_token.application
                request.user = access_token.user
                request.access_token = access_token
                return True

            return False

        except ObjectDoesNotExist:
            return False

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        """
        验证刷新token 是否有效
        :param refresh_token: 刷新token
        :param client: 客户端
        :param request: 当前请求
        :param args:
        :param kwargs:
        :return:
        """
        try:
            token = models.RefreshToken.objects.select_related('user', 'application').get(token=refresh_token)
            request.user = token.user

            # 为了避免后续再查找该请求的RefreshToken实例，将他缓存到当前请求中
            request.cache_refresh_token = token

            return token.application == client

        except ObjectDoesNotExist:
            return False

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        创建一个code
        :param client_id:客户端id
        :param code:code
        :param request:当前请求
        :param args:
        :param kwargs:
        :return:
        """
        expires = timezone.now() + timedelta(seconds=oauth_pen_settings.AUTHORIZATION_CODE_EXPIRE_SECONDS)

        models.Grant.objects.create(application=request.client,
                                    user=request.user,
                                    code=code['code'],
                                    expires=expires,
                                    redirect_uri=request.redirect_uri)

    @transaction.atomic
    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        保存token
        :param token: token
        :param request: 当前请求
        :param args:
        :param kwargs:
        :return:
        """
        expires = timezone.now() + timedelta(seconds=oauth_pen_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        refresh_token_code = token.get('refresh_token', None)

        if refresh_token_code:
            # 需要生成refresh_token的access_token
            cache_refresh_token = getattr(request, 'cache_refresh_token', None)

            if not self.rotate_refresh_token(request) and isinstance(cache_refresh_token, models.RefreshToken) and \
                    cache_refresh_token.access_token:

                # 刷新token后不变更refresh_token（直接修改之前的AccessToken，RefreshToken保持不变）
                access_token = models.AccessToken.objects.select_for_update().get(
                    pk=cache_refresh_token.access_token.pk
                )
                access_token.user = request.user
                access_token.scope = token['scope']
                access_token.expires = expires
                access_token.token = token['access_token']
                access_token.application = request.client
                access_token.save()
            else:
                # 生成一个带有refresh_token的access_token 或
                # 刷新token后变更refresh_token（删除原有的AccessToken/RefreshToken 创建新的AccessToken/RefreshToken）
                if isinstance(cache_refresh_token, models.RefreshToken):
                    try:
                        cache_refresh_token.revoke()
                    except (models.AccessToken.DoesNotExist, models.RefreshToken.DoesNotExist):
                        pass
                    else:
                        setattr(request, 'cache_refresh_token', None)

                access_token = models.AccessToken.objects.create(user=request.user,
                                                                 expires=expires,
                                                                 token=token['access_token'],
                                                                 application=request.client)

                models.RefreshToken.objects.create(user=request.user,
                                                   token=refresh_token_code,
                                                   application=request.client,
                                                   access_token=access_token)
        else:
            # 生成不需要refresh_token的access_token
            models.AccessToken.objects.create(user=request.user,
                                              expires=expires,
                                              token=token['access_token'],
                                              application=request.client)

    def rotate_refresh_token(self, request):
        """
        在刷新token成功后，返回的新的刷新token是否变化
        :param request:
        :return:
        """
        return oauth_pen_settings.ROTATE_REFRESH_TOKEN

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        让code(用于交换token的凭据) 失效
        :param client_id:
        :param code:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        grant = models.Grant.objects.get(code=code, application=request.client)
        grant.delete()

    def validate_silent_authorization(self, request):
        """
        静默授权验证
        :param request:
        :return:
        """
        # TODO 静默授权验证

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """
        验证客户端ID 是否有效
        :param client_id:客户端ID
        :param request:当前请求
        :param args:
        :param kwargs:
        :return:
        """
        return self._load_application(client_id, request) is not None

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        验证用户是否有效
        :param username:用户名
        :param password:密码
        :param client:客户端
        :param request:当前请求
        :param args:
        :param kwargs:
        :return:
        """
        try:
            user = get_user_model().objects.get(username=username)
            if user.check_password(password) and user.is_active:
                return True
        except ObjectDoesNotExist:
            return False
        else:
            return False

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        """
        检测回调地址是否有效
        :param client_id:客户端ID
        :param redirect_uri:回调地址
        :param request:当前请求
        :param args:
        :param kwargs:
        :return:
        """
        return request.client.redirect_uri_allowed(redirect_uri)

    def validate_silent_login(self, request):
        """
        验证静默登录
        :param request:
        :return:
        """
        # TODO 静默授权验证

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """
        获取默认授权范围
        :param client_id:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # TODO 获取默认授权范围

    def authenticate_client(self, request, *args, **kwargs):
        """
        验证客户端
        :param request:请求
        :param args:
        :param kwargs:
        :return:
        """
        authenticated = self._authenticate_basic_auth(request)
        if not authenticated:
            authenticated = self._authenticate_request_body(request)
        return authenticated

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """
        验证客户端ID
        :param client_id:客户端ID
        :param request:请求
        :param args:
        :param kwargs:
        :return:
        """
        if self._load_application(client_id, request) is not None:
            return request.client.client_type == ApplicationAbstract.CLIENT_PUBLIC
        return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        验证权限范围
        :param client_id: 客户端ID
        :param scopes: 权限范围
        :param client: 客户端
        :param request: 请求
        :param args:
        :param kwargs:
        :return:
        """
        # TODO 验证权限范围

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """
        验证请求中的grant_type 是否有效
        :param client_id: 客户端ID
        :param grant_type:
        :param client:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return request.client.allow_grant_type(grant_type)

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """
        验证响应的类型
        :param client_id:客户端类型
        :param response_type: code/token
        :param client:客户端
        :param request:请求
        :param args:
        :param kwargs:
        :return:
        """
        # TODO 这一步的原因
        if response_type == 'code':
            return request.client.allow_grant_type(ApplicationAbstract.GRANT_AUTHORIZATION_CODE)
        elif response_type == 'token':
            return request.client.allow_grant_type(ApplicationAbstract.GRANT_IMPLICIT)
        else:
            return False

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """
        销毁一个token
        :param token:token
        :param token_type_hint: token 实例的类型
        :param request:请求
        :param args:
        :param kwargs:
        :return:
        """
        if token_type_hint not in ['access_token', 'refresh_token']:
            token_type_hint = None

        token_types = {
            'access_token': models.AccessToken,
            'refresh_token': models.RefreshToken,
        }

        token_type = token_types.get(token_type_hint, models.AccessToken)

        token_type.objects.get(token=token).revoke()

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """
        确保回调地址的有效性
        :param client_id:
        :param code:
        :param redirect_uri:
        :param client:
        :param args:
        :param kwargs:
        :return:
        """
        grant = models.Grant.objects.get(code=code, application=client)
        return grant.redirect_uri_allowed(redirect_uri)

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """
        获取授权范围
        :param refresh_token:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # TODO 获取授权范围

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """
        获取默认回调地址
        :param client_id:客户端id
        :param request: 请求
        :param args:
        :param kwargs:
        :return:
        """
        return request.client.default_redirect_uri

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """
        验证 code
        :param client_id:
        :param code:
        :param client:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            grant = models.Grant.objects.get(code=code, application=client)
            if not grant.is_expired():
                request.user = grant.user
                request.state = grant.state
                return True
            return False
        except models.Grant.DoesNotExist:
            return False

    def validate_user_match(self, id_token_hint, scopes, claims, request):
        """
        确保token 中的user 和session中的user一致
        :param id_token_hint:
        :param scopes:
        :param claims:
        :param request:
        :return:
        """
        # TODO 确保token 中的user 和session中的user一致

    def get_id_token(self, token, token_handler, request):
        """
        open id 连接流程  还未理解
        :param token:
        :param token_handler:
        :param request:
        :return:
        """
        # TODO OPEN ID


class OAuthMixin:
    # TODO 2018-09-21 开发 server_class
    server_class = None
    validator_class = None
    backend_class = None

    def get_validator_class(self):
        self.validator_class = self.validator_class or oauth_pen_settings.OAUTH_VALIDATOR_CLASS

        if self.validator_class is None:
            raise ErrorConfigException('请配置OAUTH_VALIDATOR_CLASS或重写get_validator_class()')

        return self.validator_class

    def get_server_class(self):
        self.server_class = self.server_class or oauth_pen_settings.OAUTH_SERVER_CLASS

        if self.server_class is None:
            raise ErrorConfigException('请配置OAUTH_SERVER_CLASS或重写get_server_class()')

        return self.server_class
