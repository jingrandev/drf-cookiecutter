import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

action_done = Signal()


def log_action_done(sender, *, user, params, scope, **kwargs):
    action = kwargs.get("action")
    action_type = kwargs.get("action_type", sender)
    logger.info(
        "Action done: type=%s user=%s scope=%s%s",
        action_type.type,
        user.id if user else None,
        scope,
        f" action_id={action.id}" if action else "",
    )


action_done.connect(log_action_done)
