#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : form.py
# @Author: Pen
# @Date  : 2018-09-14 11:46
# @Desc  : 表单
from django import forms


class SuperLoginForm(forms.Form):
    user_name = forms.CharField(label='用户名', max_length=50, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super(SuperLoginForm, self).__init__(*args, **kwargs)
