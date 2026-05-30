from dependency_injector import containers
from dependency_injector import providers

from .services import EmailService
from .services import EmailTemplateService


class EmailContainer(containers.DeclarativeContainer):
    email_service = providers.Factory(EmailService)
    email_template_service = providers.Factory(
        EmailTemplateService,
        email_service=email_service,
    )
