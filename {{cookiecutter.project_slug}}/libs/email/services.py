import re
from collections.abc import Mapping
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape

from .errors import EmailSendError
from .errors import EmailTemplateError


class EmailService:
    def send_email(
        self,
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
    ) -> int:
        resolved_from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "")

        if not resolved_from_email:
            raise EmailSendError("DEFAULT_FROM_EMAIL is not configured.")

        if not to:
            raise EmailSendError("Email recipients cannot be empty.")

        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=resolved_from_email,
            to=list(to),
            cc=list(cc) if cc is not None else [],
            bcc=list(bcc) if bcc is not None else [],
            reply_to=list(reply_to) if reply_to is not None else [],
            headers=dict(headers) if headers is not None else None,
        )

        if html_body:
            message.attach_alternative(html_body, "text/html")

        try:
            return message.send(fail_silently=False)
        except Exception as exc:
            raise EmailSendError("Failed to send email.") from exc


class EmailTemplateService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    def _get_template_dir(self) -> Path:
        return Path(__file__).resolve().parent / "templates"

    def _validate_template_name(self, template_name: str) -> None:
        candidate = Path(template_name)

        if candidate.is_absolute():
            raise EmailTemplateError("Invalid template name.")

        if ".." in candidate.parts:
            raise EmailTemplateError("Invalid template name.")

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        self._validate_template_name(template_name)
        template_dir = self._get_template_dir()
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"), default_for_string=True
            ),
        )

        candidates: list[str] = [template_name]
        if "." not in Path(template_name).name:
            candidates.append(f"{template_name}.html")

        last_exc: Exception | None = None
        for name in candidates:
            try:
                template = env.get_template(name)
                return template.render(**context)
            except TemplateNotFound as exc:
                last_exc = exc

        raise EmailTemplateError(f"Template not found: {template_name}") from last_exc

    def send_template_email(
        self,
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
    ) -> int:
        html_body = self.render_template(template_name=template_name, context=context)
        body = re.sub(r"<[^>]+>", "", html_body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        return self.email_service.send_email(
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
