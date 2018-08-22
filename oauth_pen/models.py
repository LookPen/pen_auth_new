from django.db import models


class ApplicationAbstract(models.Model):
    """
    客户端信息抽象类
    """

    # 客户端类型
    CLIENT_CONFIDENTIAL = 'confidential'
    CLIENT_PUBLIC = 'public'
    CLIENT_TYPES = (
        (CLIENT_CONFIDENTIAL, 'Confidential'),
        (CLIENT_PUBLIC, 'Public'),
    )

    # 授权类型
    GRANT_AUTHORIZATION_CODE = 'authorization-code'
    GRANT_IMPLICIT = 'implicit'
    GRANT_PASSWORD = 'password'
    GRANT_CLIENT_CREDENTIALS = 'client-credentials'
    GRANT_TYPES = (
        (GRANT_AUTHORIZATION_CODE, 'Authorization code'),
        (GRANT_IMPLICIT, 'Implicit'),
        (GRANT_PASSWORD, 'Resource owner password-based'),
        (GRANT_CLIENT_CREDENTIALS, 'Client credentials'),
    )
    client_name = models.CharField('客户端名称', max_length=255, default='')
    client_id = models.CharField('客户端唯一标识', max_length=100, primary_key=True, default='TODO')
    client_secret = models.CharField('客户端密钥', max_length=255, default='TODO')
    client_type = models.CharField('客户端类型', max_length=20, choices=CLIENT_TYPES, default=CLIENT_CONFIDENTIAL)
    authorization_grant_type = models.CharField('授权类型', max_length=50, choices=GRANT_TYPES, default=GRANT_PASSWORD)
    user_id = models.CharField('创建人ID', max_length=20, default=0, db_index=True)
    skip_authorization = models.BooleanField('TODO 是否跳过授权', default=False)
    redirect_uris = models.TextField('TODO 授权成功回调地址（implicit/authorization-code 模式必填写）', blank=True)

    def __str__(self):
        return self.client_name + ':' + self.client_id

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.redirect_uris \
                and self.authorization_grant_type in (self.GRANT_IMPLICIT, self.GRANT_CLIENT_CREDENTIALS):
            raise ValidationError('{0}模式下必填写redirect_uris'.format(self.authorization_grant_type))

    class Meta:
        abstract = True


class Application(ApplicationAbstract):
    """
    客户端信息
    """
    remark = models.TextField('客户端说明',  blank=True, default='')