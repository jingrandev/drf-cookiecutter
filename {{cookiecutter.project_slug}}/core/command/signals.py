import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

command_executed = Signal()


def log_command_executed(sender, *, user, params, scope, command=None, **kwargs):
    command_type = kwargs.get("command_type", sender)
    logger.info(
        "Command executed: type=%s user=%s scope=%s%s",
        command_type.type,
        user.id if user else None,
        scope,
        f" command_id={command.id}" if command else "",
    )


command_executed.connect(log_command_executed)
