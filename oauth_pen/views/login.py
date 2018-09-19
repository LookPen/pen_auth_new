#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : login.py
# @Author: Pen
# @Date  : 2018-09-14 11:37
# @Desc  : 登录视图
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from oauth_pen.backends import AuthLibCore
from oauth_pen.form import SuperLoginForm
from oauth_pen.settings import oauth_pen_settings


class SuperLoginView(generic.FormView):
    """
    平台管理员登录
    """

    def __init__(self):
        super(SuperLoginView, self).__init__()
        self.template_name = 'admin/login.html'
        self.app_name = 'oauth_pen'
        self.index_url = reverse('pen_admin:index', current_app=self.app_name)
        self.login_url = reverse('pen_admin:login', current_app=self.app_name)

        self.form_class = SuperLoginForm
        self.redirect_field_name = oauth_pen_settings.REDIRECT_FIELD_NAME
        self.redirect_authenticated_user = True  # 已经登录过的用户进入登录页面自动跳转到get_success_url()

    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and request.user.is_authenticated:
            # 已经登录过的用户直接跳转首页
            return HttpResponseRedirect(self.index_url)

        return super(SuperLoginView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SuperLoginView, self).get_context_data(**kwargs)
        context.update({
            self.redirect_field_name: self.get_redirect_url(),
            'app_path': self.login_url
        })

        return context

    def form_valid(self, form):
        AuthLibCore(self.request).login(form.get_user())
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super(SuperLoginView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """
        获取登录成功后的跳转地址
        :return:
        """
        return self.get_redirect_url() or self.index_url

    def get_redirect_url(self):
        """
        获取请求地址中的跳转地址
        :return:
        """
        redirect_url = self.request.POST.get(self.redirect_field_name,
                                             self.request.GET.get(self.redirect_field_name, ''))

        return redirect_url


class SuperLogOutView(generic.View):
    """
    平台管理员退出登录
    """

    def __init__(self):
        super(SuperLogOutView, self).__init__()
        self.app_name = 'oauth_pen'
        self.login_url = reverse('pen_admin:login', current_app=self.app_name)

    def dispatch(self, request, *args, **kwargs):
        AuthLibCore(self.request).logout()
        return HttpResponseRedirect(self.login_url)
