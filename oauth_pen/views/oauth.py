#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : oauth.py
# @Author: Pen
# @Date  : 2018-09-19 15:08
# @Desc  : Token 的相关视图
from braces.views import CsrfExemptMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView

from oauth_pen.form import AllowForm
from oauth_pen.models import get_application_model
from oauth_pen.views.mixins import OAuthMixin, LoginRequiredMixin


class TokenView(CsrfExemptMixin, OAuthMixin):
    """
    生产token (Authorization code/Password/Client credentials)
    """

    # TODO 为啥没有简化模式
    def post(self, request, *args, **kwargs):
        """
        token 生成
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        url, headers, body, status = self.backend.create_token_response(request)

        response = HttpResponse(content=body, status=status)

        for k, v in headers.items():
            response[k] = v
        return response


class RevokeTokenView(CsrfExemptMixin, OAuthMixin):
    """
    销毁token
    """

    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.backend.create_revocation_response(request)
        response = HttpResponse(content=body or '', status=status)

        for k, v in headers:
            response[k] = v
        return response


class AuthorizationView(LoginRequiredMixin, OAuthMixin, FormView):
    """
    Authorization code /Implicit grant 模式下触发

    触发该模块流程如下：
    1.用户打开第三方应用
    2.第三方应用引导用户跳往该view的页面(get 请求)
        (1).如果用户登录了，则选择是否授权
        (2).如果没有登录的话，则重定向到登录页面，登录成功之后再重定向回来，让用户选择是否授权
    3.选择授权完成后再触发post请求（create_authorization_response）

    """
    template_name = 'oauth/allow.html'
    form_class = AllowForm
    login_url = reverse('')

    def get_initial(self):
        initial_data = {
            'redirect_uri': self.oauth2_data.get('redirect_uri', None),
            'client_id': self.oauth2_data.get('client_id', None),
            'state': self.oauth2_data.get('state', None),
            'response_type': self.oauth2_data.get('response_type', None),
        }
        return initial_data

    def form_valid(self, form):
        try:
            credentials = {
                'client_id': form.cleaned_data.get('client_id'),
                'redirect_uri': form.cleaned_data.get('redirect_uri'),
                'response_type': form.cleaned_data.get('response_type'),
                'state': form.cleaned_data.get('state')
            }

            allow = form.cleaned_data.get('allow')
            uri, headers, body, status = self.backend.create_authorization_response(request=self.request,
                                                                                    credentials=credentials,
                                                                                    allow=allow)

            self.success_url = uri

            return HttpResponseRedirect(self.success_url)

        except Exception as error:
            return self.error_response(error)

    def get(self, request, *args, **kwargs):
        """
        用户选择是否授权的页面
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            scopes, credentials = self.backend.validate_authorization_request(request)

            # 查询出数据库存在的客户端
            application = get_application_model().objects.get(client_id=credentials['client_id'])
            kwargs['application'] = application
            kwargs['client_id'] = credentials['client_id']
            kwargs['redirect_uri'] = credentials['redirect_uri']
            kwargs['response_type'] = credentials['response_type']
            kwargs['state'] = credentials['state']

            self.oauth2_data = kwargs

            form = self.get_form(self.get_form_class())
            kwargs['form'] = form

            if application.skip_authorization:
                # 跳过让用户选择授权的流程——针对内部可信任的客户端
                uri, headers, body, status = self.backend.create_authorization_response(
                    request=self.request, credentials=credentials, allow=True)
                return HttpResponseRedirect(uri)

            return self.render_to_response(self.get_context_data(**kwargs))

        except Exception as error:
            return self.error_response(error)


class AuthorizationLoginView(FormView):
    """
    选择授权前的登录界面
    """

    template_name = 'oauth/login.html'

    def get(self, request, *args, **kwargs):
        pass
        # TODO 用户登录逻辑

