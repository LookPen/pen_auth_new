#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : form.py
# @Author: Pen
# @Date  : 2018-09-14 11:46
# @Desc  : 表单
from django import forms

from oauth_pen.backends import AuthLibCore


class SuperLoginForm(forms.Form):
    username = forms.CharField(
        label='用户名',
        max_length=50,
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'layui-input'}))

    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'layui-input'}))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None  # 只计算一次当前登录的帐号
        super(SuperLoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = AuthLibCore(self.request).authenticate({'username': username, 'password': password})
            if self.user_cache is None:
                raise forms.ValidationError('用户名密码错误')

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class AllowForm(forms.Form):
    """
    用户选择是否允许授权的表单（Authorization code /Implicit grant 模式）
    """
    allow = forms.BooleanField(required=False)
    redirect_uri = forms.CharField(widget=forms.HiddenInput())
    scope = forms.CharField(widget=forms.HiddenInput())
    client_id = forms.CharField(widget=forms.HiddenInput())
    state = forms.CharField(required=False, widget=forms.HiddenInput())
    response_type = forms.CharField(widget=forms.HiddenInput())
