#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : signals.py
# @Author: Pen
# @Date  : 2018-09-18 17:07
# @Desc  : 信号量
from django.dispatch import Signal

user_login_failed = Signal(providing_args=['credentials', 'request'])  # 用户登录失败触发信号
user_login_success = Signal(providing_args=['user', 'request'])  # 用户登录成功触发信号
user_logout_success = Signal(providing_args=['user', 'request'])  # 用户退出登录触发信号
