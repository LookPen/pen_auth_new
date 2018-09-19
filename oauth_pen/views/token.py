#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : token.py
# @Author: Pen
# @Date  : 2018-09-19 15:08
# @Desc  : Token 的相关视图
from braces.views import CsrfExemptMixin

from oauth_pen.oauth import OAuthMixin


class TokenView(CsrfExemptMixin, OAuthMixin):
    # TODO 1
    pass
