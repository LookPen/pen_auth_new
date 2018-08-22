#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : application.py
# @Author: Pen
# @Date  : 2018-08-17 15:27
# @Desc  : application 管理页面
# from braces.views import LoginRequiredMixin
import json

from django.forms import modelform_factory
from django.http import HttpResponse
from django.views import generic, View
from django.shortcuts import render
from oauth_pen.settings import oauth_pen_settings


class CurrentUserApplicationMixin():
    """
    当前用户创建的Application
    """

    fields = '__all__'

    def get_queryset(self):
        return oauth_pen_settings.APPLICATION_MODEL.objects.all()


class ApplicationDetail(CurrentUserApplicationMixin, generic.DetailView):
    """
    客户端详情
    """
    context_object_name = 'application'
    template_name = 'application/application_detail.html'


class ApplicationAdd(generic.CreateView):
    template_name = 'application/application_detail.html'

    def get_form_class(self):
        return oauth_pen_settings.APPLICATION_MODEL

    def form_valid(self, form):
        form.instance.user_id = self.request.user.pk
        return super(ApplicationAdd, self).form_invalid(form)


class ApplicationUpdate(CurrentUserApplicationMixin, generic.UpdateView):
    context_object_name = 'application'
    template_name = 'application/application_form.html'

    def get_form_class(self):
        fields = modelform_factory(
            oauth_pen_settings.APPLICATION_MODEL,
            exclude=('user_id',)
        )

        for f in fields.base_fields:
            if f not in ('skip_authorization',):
                fields.base_fields[f].widget.attrs['class'] = 'form-control'
            if f in ('client_id', 'client_secret'):
                fields.base_fields[f].widget.attrs['readonly'] = 'readonly'

        return fields


def app_page(request):
    return render(request, 'application/applications.html')


class ApiApplication(View):
    def get(self, request):
        data = oauth_pen_settings.APPLICATION_MODEL.objects.values('client_id', 'client_name', 'client_type',
                                                                   'authorization_grant_type', 'remark')

        return HttpResponse(json.dumps({
            'count': len(data),
            'code': 0,
            'msg': '',
            'data': list(data)
        }))
