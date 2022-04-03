from __future__ import annotations

from typing import Any, Sequence, TypeVar  # noqa: F401
from decimal import Decimal

from apgorm import Database, Model, types, Converter

from .config import CONFIG


_T = TypeVar("_T")


class DecimalIntArray(Converter["Sequence[Decimal | None]", "Sequence[int]"]):
    def to_stored(self, value: Sequence[int]) -> Sequence[Decimal]:
        return [Decimal(v) for v in value]

    def from_stored(self, value: Sequence[Decimal | None]) -> Sequence[int]:
        return [int(v) for v in value if v is not None]


class Guild(Model):
    id = types.Numeric().field()
    allowed_channels = (
        types.Array(types.Numeric()).field().with_converter(DecimalIntArray())
    )
    blacklisted_roles = (
        types.Array(types.Numeric()).field().with_converter(DecimalIntArray())
    )

    primary_key = (id,)


class DB(Database):
    def __init__(self) -> None:
        super().__init__("music/migrations")

    async def connect(self, **kwargs: Any) -> None:
        await super().connect(
            database=CONFIG.db_name,
            user=CONFIG.db_user,
            password=CONFIG.db_password,
            host="localhost",
        )
        if self.must_create_migrations():
            raise Exception("There are uncreated migrations.")
        if await self.must_apply_migrations():
            print("Applying migrations...")
            await self.apply_migrations()

    guilds = Guild
