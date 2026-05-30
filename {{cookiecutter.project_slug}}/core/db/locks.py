from typing import Type

from django.db import DEFAULT_DB_ALIAS
from django.db import models
from django.db.transaction import Atomic


class LockedAtomicTransaction(Atomic):
    """Wraps ``transaction.atomic()`` with a full table lock.

    Entering the context manager acquires an **exclusive** table-level
    lock (``LOCK TABLE ... IN EXCLUSIVE MODE`` on PostgreSQL, ``LOCK
    TABLES ... WRITE`` on MySQL) so that no other transaction can read
    *or* write the table until this block exits.

    Use with caution — table-level locks block all concurrent access
    and have a direct impact on throughput.  Prefer ``select_for_update()``
    (row-level lock) when possible and only reach for this when you
    genuinely need to serialise access to an entire table.

    Usage::

        with LockedAtomicTransaction(MyModel):
            MyModel.objects.create(...)
    """

    def __init__(
        self,
        model: Type[models.Model],
        using: str | None = None,
        savepoint: bool = True,
        durable: bool = False,
    ) -> None:
        self.model = model
        super().__init__(using or DEFAULT_DB_ALIAS, savepoint, durable)

    def __enter__(self) -> None:
        super().__enter__()
        self._lock_table()

    def _lock_table(self) -> None:
        db_table = self.model._meta.db_table
        connection = self.connection

        vendor = connection.vendor
        cursor = connection.cursor()
        try:
            if vendor == "postgresql":
                cursor.execute(
                    f'LOCK TABLE "{db_table}" IN EXCLUSIVE MODE'
                )
            elif vendor == "mysql":
                cursor.execute(
                    f'LOCK TABLES `{db_table}` WRITE'
                )
            else:
                raise NotImplementedError(
                    f"LockedAtomicTransaction does not support {vendor}"
                )
        finally:
            cursor.close()
