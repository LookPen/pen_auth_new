#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : exceptions.py
# @Author: Pen
# @Date  : 2018-08-17 16:48
# @Desc  : 异常类


class ErrorConfigException(Exception):
    """
    配置错误
    """
    pass


class NoPermissionException(Exception):
    """没有权限访问"""
    pass
