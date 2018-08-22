#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : urls.py
# @Author: Pen
# @Date  : 2018-08-17 15:16
# @Desc  : oauth_pen 路由

from django.conf.urls import url
from oauth_pen.views import application

# 管理页面地址
management_urlpatterns = [
    # url(r'^application/(?P<pk>.*)/edit$', application.ApplicationUpdate.as_view(), name='update'),
    # url(r'^application/(?P<pk>.*)$', application.ApplicationDetail.as_view(), name='detail'),

    url(r'^applications', application.app_page),
    url(r'^api/app_list$', application.ApiApplication.as_view())

]

urlpatterns = management_urlpatterns
