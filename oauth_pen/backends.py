#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : backends.py
# @Author: Pen
# @Date  : 2018-09-14 15:56
# @Desc  : 后台逻辑 (由于该项目重点是在OAuth2.0 上，所以平台自身管理员帐号 将直接使用配置文件配置)

from oauth_pen import models
from oauth_pen.models import SuperUser
from oauth_pen.settings import oauth_pen_settings

SESSION_KEY = '_pen_auth_user'
HASH_SESSION_KEY = '_pen_auth_user_hash'


class AuthMixin:
    def __init__(self, request):
        self.request = request
        self.user_id = None

    def get_user(self):
        """
        获取当前请求的用户
        :param request: 当前请求
        :return:
        """
        return models.AnonymousUser()


class AuthLibCore(AuthMixin):
    def __init__(self, request):
        super(AuthLibCore, self).__init__(request)
        self.admin_user = SuperUser()

    def get_user(self):
        """
        获取当前请求的用户
        :return:
        """
        user = None

        try:
            self.user_id = self.request.session[SESSION_KEY]
        except:
            pass
        else:
            # 平台自身管理员是通过配置文件配置/user_id的获取逻辑是放在session模块中的
            if self.admin_user.id == self.user_id:
                user = self.admin_user

            # 验证session
            if hasattr(user, 'get_session_auth_hash'):
                session_hash = self.request.session.get(HASH_SESSION_KEY)
                if session_hash and

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
