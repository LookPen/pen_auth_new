#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : login.py
# @Author: Pen
# @Date  : 2018-09-14 11:37
# @Desc  : 登录视图
from django.views import generic
from django.views.generic import FormView


class SuperLogin(FormView):
    """
    超级管理员登录
    """

