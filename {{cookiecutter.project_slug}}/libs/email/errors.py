from django.utils.translation import gettext_lazy as _
from rest_framework import status

from core.restframework.error_handler import BaseError


class EmailError(BaseError):
    code = "EMAIL_1000"
    message = _("Email error")
    http_status = status.HTTP_400_BAD_REQUEST


class EmailSendError(EmailError):
    code = "EMAIL_1001"
    message = _("Failed to send email")
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR


class EmailTemplateError(EmailError):
    code = "EMAIL_1002"
    message = _("Invalid email template")
    http_status = status.HTTP_400_BAD_REQUEST
