#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : application.py
# @Author: Pen
# @Date  : 2018-08-17 15:27
# @Desc  : application 管理页面
# from braces.views import LoginRequiredMixin
import json
from django.forms import modelform_factory, model_to_dict
from django.http import HttpResponse
from django.views import generic, View
from django.shortcuts import render
from oauth_pen.settings import oauth_pen_settings
from oauth_pen import models


def app_page(request):
    return render(request, 'application/application.html')


class ApiApplication(View):
    def get(self, request):
        """
        获取客户端信息
        :param request:
        :return:
        """
        client_id = request.GET.get('client_id', None)

        if client_id:
            # 详情
            data = oauth_pen_settings.APPLICATION_MODEL.objects.filter(client_id=client_id).first()
            data = model_to_dict(data)
            return HttpResponse(json.dumps(data))

        else:
            # 列表
            data = oauth_pen_settings.APPLICATION_MODEL.objects.values('client_id', 'client_name', 'client_type',
                                                                       'authorization_grant_type', 'remark')
            return HttpResponse(json.dumps({
                'count': len(data),
                'code': 0,
                'msg': '',
                'data': list(data)
            }))

    def post(self, request):
        """
        修改客户端信息
        :param request:
        :return:
        """
        user_id = 0  # request.user.pk
        client_name = request.POST.get('client_name', None)
        client_id = request.POST.get('client_id', None)
        client_secret = request.POST.get('client_secret', None)
        client_type = request.POST.get('client_type', None)
        authorization_grant_type = request.POST.get('authorization_grant_type', None)
        skip_authorization = request.POST.get('skip_authorization', 'off')
        skip_authorization = True if skip_authorization == 'on' else False
        redirect_uris = request.POST.get('redirect_uris', None)
        remark = request.POST.get('remark', None)

        if None in (client_name, client_id, client_secret, client_type, authorization_grant_type, skip_authorization):
            return HttpResponse('参数错误', status=400)
        if authorization_grant_type in (
                models.Application.GRANT_IMPLICIT, models.Application.GRANT_AUTHORIZATION_CODE) and not redirect_uris:
            return HttpResponse('{} 模式下,回调地址必填'.format(authorization_grant_type), status=400)

        data = oauth_pen_settings.APPLICATION_MODEL.objects.filter(client_id=client_id).first()
        if not data:
            return HttpResponse('客户端不存在', status=400)

        data = oauth_pen_settings.APPLICATION_MODEL.objects.filter(client_id=client_id).first()

        if not data:
            data = oauth_pen_settings.APPLICATION_MODEL()

        data.client_name = client_name
        data.client_type = client_type
        data.authorization_grant_type = authorization_grant_type
        data.skip_authorization = skip_authorization
        data.redirect_uris = redirect_uris
        data.remark = remark
        data.user_id = user_id
        data.save()

        return HttpResponse(json.dumps(model_to_dict(data)))
