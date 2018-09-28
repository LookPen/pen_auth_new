#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : middleware.py
# @Author: Pen
# @Date  : 2018-09-14 15:12
# @Desc  : 中间件
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from oauth_pen.exceptions import ErrorConfigException
from oauth_pen import backends


def get_user(request):
    """
    用户获取
    :param request:当前请求
    :return:
    """
    if not hasattr(request, '_cache_user'):
        if request.session.get(backends.SUPER_SESSION_KEY):
            request._cache_user = backends.AuthLibCore(request).get_user()
        else:
            request._cache_user = backends.PenOAuthLibCore(request).get_user()

    return request._cache_user


class AuthenticationMiddleware(MiddlewareMixin):
    """
    权限认证中间件
    """
    def process_request(self, request):
        if not hasattr(request, 'session'):
            raise ErrorConfigException(
                'AuthenticationMiddleware中间件 依赖django.contrib.sessions.middleware.SessionMiddleware，请在MIDDLEWARE中配置')

        request.user = SimpleLazyObject(lambda: get_user(request))
