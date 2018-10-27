#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : application.py
# @Author: Pen
# @Date  : 2018-08-17 15:27
# @Desc  : application 管理页面
# from braces.views import LoginRequiredMixin
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from oauth_pen import models
from oauth_pen.settings import oauth_pen_settings
from oauth_pen.views.mixins import SuperUserRequiredMixin


class Application(SuperUserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        url = reverse('pen_admin:index')
        url = url.strip('/').split('/')[0]  # 请求的根路径是用户自定义的
        return render(self.request, 'application/application.html', {'url_root': '/' + url})


class ApiApplicationList(SuperUserRequiredMixin, View):
    def get(self, request):
        """
        获取客户端列表
        :return:
        """
        data = models.get_application_model().objects.all()
        result = []
        for d in data:
            result.append({
                'client_id': d.client_id,
                'client_name': d.client_name,
                'client_type': d.get_client_type_display(),
                'authorization_grant_type': d.get_authorization_grant_type_display(),
                'remark': d.remark
            })
        return JsonResponse({
            'count': len(result),
            'code': 0,
            'msg': '',
            'data': list(result)
        })


class ApiApplication(SuperUserRequiredMixin, View):
    def get(self, request):
        """
        获取客户端信息
        :return:
        """
        client_id = self.request.GET.get('client_id', None)

        data = models.get_application_model().objects.filter(client_id=client_id).first()
        if data:
            data = model_to_dict(data)
        else:
            application_class = models.get_application_model()
            data = model_to_dict(application_class())

        return JsonResponse(data)

    def post(self, request):
        """
        修改/添加客户端信息
        :return:
        """
        application_class = models.get_application_model()

        user_id = 0  # request.user.pk
        client_name = self.request.POST.get('client_name', None)
        client_id = self.request.POST.get('client_id', None)
        client_secret = self.request.POST.get('client_secret', None)
        client_type = self.request.POST.get('client_type', None)
        authorization_grant_type = self.request.POST.get('authorization_grant_type', None)
        skip_authorization = self.request.POST.get('skip_authorization', 'off')
        skip_authorization = True if skip_authorization == 'on' else False
        redirect_uris = self.request.POST.get('redirect_uris', None)
        remark = self.request.POST.get('remark', None)

        if None in (client_name, client_id, client_secret, client_type, authorization_grant_type, skip_authorization):
            return HttpResponse('参数错误', status=400)

        if authorization_grant_type in (
                models.Application.GRANT_IMPLICIT, models.Application.GRANT_AUTHORIZATION_CODE) and not redirect_uris:
            return HttpResponse('{} 模式下,回调地址必填'.format(authorization_grant_type), status=400)

        data = application_class.objects.filter(client_id=client_id).first()
        if not data:
            data = application_class()

        data.client_id = client_id
        data.client_secret = client_secret
        data.client_name = client_name
        data.client_type = client_type
        data.authorization_grant_type = authorization_grant_type
        data.skip_authorization = skip_authorization
        data.redirect_uris = redirect_uris
        data.remark = remark
        data.user_id = user_id
        data.save()

        return JsonResponse(model_to_dict(data))

    def delete(self, request):
        """
        删除客户端
        :param request:
        :return:
        """
        client_id = self.request.GET.get('client_id', None)
        data = models.get_application_model().objects.filter(client_id=client_id).first()
        if data:
            data.delete()

        return JsonResponse({'status': 'success'})
