#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : access.py
# @Author: Pen
# @Date  : 2018-09-14 10:22
# @Desc  : 检测当前请求是否有权限
import inspect
from urllib.parse import urlparse, urlunparse
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.urls import reverse
from oauth_pen.exceptions import ErrorConfigException
from oauth_pen.settings import oauth_pen_settings


class AccessMixin:
    def __init__(self):
        self.login_url = None  # 登录地址
        self.raise_exception = None  # 没有权限的时候抛出的异常获取处理的函数
        self.redirect_field_name = oauth_pen_settings.REDIRECT_FIELD_NAME  # 登录成功后，url中代表跳转地址参数的key

        self.get_login_url()
        self.get_redirect_field_name()

    def get_login_url(self):
        """
        获取登录地址

        :return:
        """
        self.login_url = self.login_url or oauth_pen_settings.LOGIN_URL

        if not self.login_url:
            raise ErrorConfigException('请配置LOGIN_URL 或重写get_login_url方法')

        return self.login_url

    def get_redirect_field_name(self):
        """
        获取登录成功后，url中代表跳转地址参数的key

        :return:
        """
        self.redirect_field_name = self.redirect_field_name or oauth_pen_settings.REDIRECT_FIELD_NAME

        if not self.redirect_field_name:
            raise ErrorConfigException('请配置REDIRECT_FIELD_NAME 或重写get_redirect_field_name方法')

        return self.redirect_field_name

    def handle_no_permission(self, request):
        """
        没有权限的时候的处理逻辑

        :return:
        """
        if self.raise_exception and inspect.isclass(self.raise_exception) and issubclass(self.raise_exception,
                                                                                         Exception):
            raise self.raise_exception
        elif callable(self.raise_exception):
            result = self.raise_exception(request)
            if isinstance(result, HttpResponse):
                # 如果是http响应结果 就直接返回
                return result
        else:
            return self.redirect_to_login(request.get_full_path())

    def redirect_to_login(self, next_url):
        """
        跳转到登录页面

        :param next_url: 登录成功之后的跳转地址
        :return:
        """
        url_parts = list(urlparse(self.login_url))

        if url_parts:
            query_dict = QueryDict(url_parts[4], mutable=True)
            query_dict[self.redirect_field_name] = next_url
            url_parts[4] = query_dict.urlencode()

        return HttpResponseRedirect(urlunparse(url_parts))


class LoginRequiredMixin(AccessMixin):
    """
    view 的mixin类 当前请求必须登录后才能操作

    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return self.handle_no_permission(request)

        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class SuperUserRequiredMixin(AccessMixin):
    """
    view 的mixin类 当前请求必须是平台管理员才能操作
    """

    def get_login_url(self):
        """
        获取登录地址

        :return:
        """
        self.login_url = reverse('pen_admin:login', current_app='oauth_pen')

        return self.login_url

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_super:
            return super(SuperUserRequiredMixin, self).dispatch(request, *args, **kwargs)

        return self.handle_no_permission(request)
