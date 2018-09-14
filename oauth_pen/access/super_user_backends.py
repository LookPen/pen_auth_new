#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : super_user_backends.py
# @Author: Pen
# @Date  : 2018-09-14 11:29
# @Desc  : 超级管理员的逻辑（由于该项目重点是在OAuth2.0 上，所以超级管理员帐号 将直接使用配置文件配置）

# TODO 超级管理员的相关逻辑

class SuperUser:
    def __init__(self, request):
        self.request = request

    @property
    def user_name(self):
        return 'Pen'

    @property
    def is_super_user(self):
        return True
