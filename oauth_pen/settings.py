#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : settings.py
# @Author: Pen
# @Date  : 2018-08-17 13:56
# @Desc  :oauth_pen 的配置文件
import importlib

from django.conf import settings
from oauth_pen import exceptions

USER_SETTINGS = getattr(settings, 'OAUTH_PEN', None)  # 允许用户配置覆盖默认配置

# 默认配置
DEFAULTS = {
    'APPLICATION_MODEL': 'oauth_pen.models.Application',  # 客户端信息
    'REDIRECT_FIELD_NAME': 'next',  # 登录成功后，url中代表跳转地址参数的key
    'ADMIN_NAME': 'Pen',  # 平台管理员帐号
    'ADMIN_PASSWORD': 'Pen',  # 平台管理员密码
    'LOGIN_URL': '',  # 请填写完整的路由，如果为空表示使用系统默认登录界面
    'AUTH_USER_MODEL': 'oauth_pen.models.User',  # 用户信息
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 60,  # Code 过期时间 单位 秒
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,  # token 过期时间 单位 秒
    'ROTATE_REFRESH_TOKEN': True,  # 刷新token成功后 refresh_token是否变更

    'OAUTH_VALIDATOR_CLASS': ''  # TODO
}

# 如果以下配置是字符串的形式，则进行反射处理
IMPORT_STRINGS = [
    'APPLICATION_MODEL',
    'AUTH_USER_MODEL',
    'OAUTH_VALIDATOR_CLASS',
    'AUTHENTICATION_BACKEND'
]


class OAuthPenSetting:
    def __init__(self, user_setting=None, default=None):
        self.user_setting = user_setting or {}
        self.default = default or {}

    def __getattr__(self, item):
        if item not in DEFAULTS.keys():
            raise AttributeError('未定义{0}'.format(item))

        try:
            # 用户配置优先
            value = self.user_setting[item]
        except:
            value = self.default[item]

        # 导入的是以字符串的形似配置
        if item in IMPORT_STRINGS:
            value = self.import_from_string(value)

        # 保存值
        setattr(self, item, value)

        return value

    @classmethod
    def import_from_string(cls, item):
        """
        导入字符串形似的模板
        :param item: app_name.model_name
        :return:
        """
        try:
            parts = item.split('.')

            module_path, class_name = '.'.join(parts[:-1]), parts[-1]

            modules = importlib.import_module(module_path)

            return getattr(modules, class_name)

        except Exception as e:
            raise exceptions.ErrorConfigException(item + ' 配置无效', e)


oauth_pen_settings = OAuthPenSetting(USER_SETTINGS, DEFAULTS)
