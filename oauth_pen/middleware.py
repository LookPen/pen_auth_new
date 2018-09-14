#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : middleware.py
# @Author: Pen
# @Date  : 2018-09-14 15:12
# @Desc  : 中间件
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from oauth_pen.exceptions import ErrorConfigException


def get_user(request):
    if not hasattr(request, '_cache_user'):
        request._cache_user = None  # TODO 获取请求的用户
    return request._cache_user


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, 'session'):
            raise ErrorConfigException(
                'AuthenticationMiddleware中间件 依赖django.contrib.sessions.middleware.SessionMiddleware，请在MIDDLEWARE中配置')

        request.user = SimpleLazyObject(lambda: get_user(request))
