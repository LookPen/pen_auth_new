#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : backends.py
# @Author: Pen
# @Date  : 2018-09-14 15:56
# @Desc  : 后台逻辑 (由于该项目重点是在OAuth2.0 上，所以平台自身管理员帐号 将直接使用配置文件配置)

from oauth_pen import models
from oauth_pen.settings import oauth_pen_settings


class AuthMixin:
    def __init__(self, request):
        self.request = request
        self.user_id = request.session[oauth_pen_settings.SESSION_KEY]

    def get_user(self):
        """
        获取当前请求的用户
        :param request: 当前请求
        :return:
        """
        pass


# TODO 平台自身权限的相关逻辑
class AuthLibCore(AuthMixin):
    def __init__(self, request):
        super(AuthLibCore, self).__init__(request)

        self.admin_user = {'id': '1',
                           'username': oauth_pen_settings.ADMIN_NAME,
                           'password': oauth_pen_settings.ADMIN_PASSWORD}  # 通过配置文件配置管理员帐号

    @property
    def is_super_user(self):
        return True

    def get_user(self):
        """
        获取当前请求的用户
        :return:
        """
        user = None
        # TODO 2018-9-14

        return user or models.AnonymousUser()


class PenOAuthLibCore(AuthMixin):
    def get_user(self):
        """
        获取用户实体

        :param request:当前请求
        :return:
        """
        user = None
        # TODO 获取用户实体

        return user or models.AnonymousUser()
