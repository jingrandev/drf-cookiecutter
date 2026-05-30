from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any

from celery import shared_task
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject

from .di_containers import EmailContainer
from .services import EmailService
from .services import EmailTemplateService


@shared_task(name="email.send_email")
@inject
def send_email_task(
    *,
    subject: str,
    body: str,
    to: Sequence[str],
    from_email: str | None = None,
    html_body: str | None = None,
    cc: Sequence[str] | None = None,
    bcc: Sequence[str] | None = None,
    reply_to: Sequence[str] | None = None,
    headers: Mapping[str, str] | None = None,
    email_service: EmailService = Provide[EmailContainer.email_service],
) -> int:
    return email_service.send_email(
        subject=subject,
        body=body,
        to=to,
        from_email=from_email,
        html_body=html_body,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        headers=headers,
    )


@shared_task(name="email.send_template_email")
@inject
def send_template_email_task(
    *,
    subject: str,
    template_name: str,
    context: dict[str, Any],
    to: Sequence[str],
    from_email: str | None = None,
    cc: Sequence[str] | None = None,
    bcc: Sequence[str] | None = None,
    reply_to: Sequence[str] | None = None,
    headers: Mapping[str, str] | None = None,
    template_service: EmailTemplateService = Provide[
        EmailContainer.email_template_service
    ],
) -> int:
    return template_service.send_template_email(
        subject=subject,
        template_name=template_name,
        context=context,
        to=to,
        from_email=from_email,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        headers=headers,
    )
