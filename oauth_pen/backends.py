#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : backends.py
# @Author: Pen
# @Date  : 2018-09-14 15:56
# @Desc  : 后台逻辑 (由于该项目重点是在OAuth2.0 上，所以平台自身管理员帐号 将直接使用配置文件配置)
from urllib.parse import urlparse, urlunparse
from oauthlib import oauth2
from oauthlib.common import urlencode, urlencoded, quote

from django.utils.crypto import constant_time_compare

from oauth_pen import models
from oauth_pen import signals
from oauth_pen.exceptions import NoPermissionException
from oauth_pen.models import get_user_model

SESSION_KEY = '_pen_auth_user'
HASH_SESSION_KEY = '_pen_auth_user_hash'
SUPER_SESSION_KEY = '_pen_auth_super'


class AuthMixin:
    def __init__(self, request):
        self.request = request
        self.user_id = None

    def get_user(self):
        """
        获取当前请求的用户
        :return:
        """
        return models.AnonymousUser()


class AuthLibCore(AuthMixin):
    """
    平台自身认证
    """

    def __init__(self, request):
        super(AuthLibCore, self).__init__(request)
        self.admin_user = models.SuperUser()

    def get_user(self):
        """
        获取当前请求的用户
        :return:
        """
        user = None

        try:
            self.user_id = self.request.session[SESSION_KEY]  # user_id的获取逻辑是放在session模块中的
        except:
            pass
        else:
            # 平台自身管理员是通过配置文件配置
            if self.admin_user.user_id == self.user_id:
                user = self.admin_user

            # 验证session
            if hasattr(user, 'get_session_auth_hash'):
                session_hash = self.request.session.get(HASH_SESSION_KEY)
                if not session_hash or not constant_time_compare(session_hash, user.get_session_auth_hash()):
                    self.request.session.flush()  # 当前session 无效 清空session
                    user = None

        return user or models.AnonymousUser()

    def authenticate(self, credentials):
        """
        验证是否有效用户，并返回用户实体
        :param credentials:用户凭证
        :return:
        """
        username = credentials.get('username', None)
        password = credentials.get('password', None)

        if self.admin_user.username == username and self.admin_user.password == password:  # 简单的判断一下用户名密码
            return self.admin_user

        # 登录失败信号
        signals.user_login_failed.send(sender=__name__,
                                       credentials={'username': username, 'password': password},
                                       request=self.request)

    def login(self, user):
        """
        登录
        :param user: 已经通过验证的用户
        :return:
        """
        session_auth_hash = user.get_session_auth_hash()

        if SESSION_KEY in self.request.session:
            # 避免不用的用户使用相同的session key
            if self.request.session[SESSION_KEY] != user.user_id or not \
                    constant_time_compare(session_auth_hash, self.request.session.get(HASH_SESSION_KEY, '')):
                self.request.session.flush()
        else:
            # 新建一个session key
            self.request.session.cycle_key()

        self.request.session[SESSION_KEY] = user.user_id
        self.request.session[HASH_SESSION_KEY] = session_auth_hash
        self.request.session[SUPER_SESSION_KEY] = True
        self.request.user = user

        # 登录成功信号
        signals.user_login_success.send(sender=__name__, request=self.request, user=user)

    def logout(self):
        user = self.request.user
        self.request.session.flush()  # 清除session
        self.request.user = models.AnonymousUser()

        # 发送退出登录的信号
        signals.user_logout_success.send(sender=__name__, request=self.request, user=user)


class PenOAuthLibCore(AuthMixin):
    """
    oauth_pen 认证
    """

    def __init__(self, request, validator=None):
        """

        :param validator:
        """
        super(PenOAuthLibCore, self).__init__(request)

        self.validator = validator
        self.server = oauth2.Server(validator)

    @classmethod
    def _get_escaped_full_path(cls, request):
        """
        获取安全的url
        :param request:
        :return:
        """
        parsed = list(urlparse(request.get_full_path()))

        unsafe = set(c for c in parsed[4]).difference(urlencoded)

        for c in unsafe:
            parsed[4] = parsed[4].replace(c, quote(c, safe=b''))

        return urlunparse(parsed)

    @classmethod
    def _extract_headers(cls, request):
        """
        获取request 头
        :param request:
        :return:
        """
        headers = request.META.copy()

        # 在common.to_unicode() 时转不了，那就把你们删了吧
        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']

        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']

        return headers

    @classmethod
    def _extract_body(cls, request):
        """
        提取request 中的body
        :param request:
        :return:
        """
        return request.POST.items()

    def _extract_params(self, request):
        """
        提取request 中的参数
        :param request:
        :return:
        """
        uri = self._get_escaped_full_path(request)
        http_method = request.method
        headers = self._extract_headers(request)
        body = urlencode(self._extract_body(request))
        return uri, http_method, body, headers

    def validate_authorization_request(self, request):
        uri, http_method, body, headers = self._extract_params(request)
        scopes, credentials = self.server.validate_authorization_request(uri, http_method=http_method, body=body,
                                                                         headers=headers)

        return scopes, credentials

    def create_authorization_response(self, request, scopes, credentials, allow):
        if not allow:
            raise NoPermissionException()

        credentials['user'] = request.user
        headers, body, status = self.server.create_authorization_response(uri=credentials['redirect_uri'],
                                                                          scopes=scopes, credentials=credentials)
        uri = headers.get("Location", None)

        return uri, headers, body, status

    def create_token_response(self, request):
        uri, http_method, body, headers = self._extract_params(request)

        headers, body, status = self.server.create_token_response(uri, http_method, body,
                                                                  headers, {})
        uri = headers.get("Location", None)

        return uri, headers, body, status

    def create_revocation_response(self, request):
        uri, http_method, body, headers = self._extract_params(request)

        headers, body, status = self.server.create_revocation_response(
            uri, http_method, body, headers)
        uri = headers.get("Location", None)

        return uri, headers, body, status

    def verify_request(self, request, scopes):
        uri, http_method, body, headers = self._extract_params(request)

        valid, r = self.server.verify_request(uri, http_method, body, headers, scopes=scopes)
        return valid, r

    def get_user(self):
        """
        获取用户实体

        :param
        :return:
        """
        user = None

        try:
            self.user_id = self.request.session[SESSION_KEY]
            user = get_user_model().objects.get(pk=self.user_id)
        except:
            pass

            # 验证session
            if hasattr(user, 'get_session_auth_hash'):
                session_hash = self.request.session.get(HASH_SESSION_KEY)
                if not session_hash or not constant_time_compare(session_hash, user.get_session_auth_hash()):
                    self.request.session.flush()  # 当前session 无效 清空session
                    user = None

        return user or models.AnonymousUser()
