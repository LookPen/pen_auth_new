#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : backends.py
# @Author: Pen
# @Date  : 2018-09-14 15:56
# @Desc  : 后台逻辑 (由于该项目重点是在OAuth2.0 上，所以平台自身管理员帐号 将直接使用配置文件配置)
from django.utils.crypto import constant_time_compare

from oauth_pen import models
from oauth_pen.models import SuperUser
from oauth_pen import signals

SESSION_KEY = '_pen_auth_user'
HASH_SESSION_KEY = '_pen_auth_user_hash'


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
        self.admin_user = SuperUser()

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

    def authenticate(self, username, password):
        """
        验证是否有效用户，并返回用户实体
        :param username:用户名
        :param password:密码
        :return:
        """
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
        self.request.user = user

        # 登录成功信号
        signals.user_login_success.send(sender=__name__, request=self.request, user=user)


class PenOAuthLibCore(AuthMixin):
    """
    oauth_pen 认证
    """

    def get_user(self):
        """
        获取用户实体

        :param request:当前请求
        :return:
        """
        user = None
        # TODO 获取用户实体

        return user or models.AnonymousUser()
