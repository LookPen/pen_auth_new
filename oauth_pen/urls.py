#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : urls.py
# @Author: Pen
# @Date  : 2018-08-17 15:16
# @Desc  : oauth_pen 路由

from django.conf.urls import url
from oauth_pen.views import application
from oauth_pen.views import login

# 管理界面
management_urlpatterns = [
    url(r'^index$', application.Application.as_view(), name='index'),
    url(r'^login$', login.SuperLoginView.as_view(), name='login')
]

api_urlpatterns = [
    url(r'^api/app$', application.ApiApplication.as_view()),
    url(r'^api/app_list$', application.ApiApplicationList.as_view())
]

urlpatterns = management_urlpatterns + api_urlpatterns
