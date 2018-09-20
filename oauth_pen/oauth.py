#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : oauth.py
# @Author: Pen
# @Date  : 2018-09-19 15:27
# @Desc  : oauth授权Mixin
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from oauthlib.oauth2 import RequestValidator

from oauth_pen.exceptions import ErrorConfigException
from oauth_pen import models
from oauth_pen.models import get_application_model, get_user_model
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


        except ObjectDoesNotExist:
            return False

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        pass

    def validate_silent_login(self, request):
        pass

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        pass

    def authenticate_client(self, request, *args, **kwargs):
        pass

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        pass

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        pass

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        pass

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        pass

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        pass

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        pass

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        pass

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        pass

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        pass

    def validate_user_match(self, id_token_hint, scopes, claims, request):
        pass

    def get_id_token(self, token, token_handler, request):
        pass


class OAuthMixin:
    # TODO 2
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
