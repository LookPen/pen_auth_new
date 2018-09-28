#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : site.py
# @Author: Pen
# @Date  : 2018-09-18 14:20
# @Desc  : 路由

from django.conf.urls import url
from oauth_pen.views import application
from oauth_pen.views import login, oauth


class PenAdmin:
    @property
    def urls(self):
        # 管理界面
        management_urlpatterns = [
            url(r'^index$', application.Application.as_view(), name='index'),
            url(r'^login$', login.SuperLoginView.as_view(), name='login'),
            url(r'^logout$', login.SuperLogOutView.as_view(), name='logout')
        ]

        # 授权界面
        auth_urlpatterns = [
            url(r'^auth_login', oauth.AuthorizationLoginView.as_view(), name='auth_login'),  # 选择授权前的登录界面
            url(r'^auth', oauth.AuthorizationView.as_view(), name='auth')
        ]

        # api接口
        api_urlpatterns = [
            url(r'^api/app$', application.ApiApplication.as_view()),
            url(r'^api/app_list$', application.ApiApplicationList.as_view())
        ]

        urlpatterns = management_urlpatterns + auth_urlpatterns + api_urlpatterns

        return urlpatterns, 'admin', 'pen_admin'


pen_site = PenAdmin()
