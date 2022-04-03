from __future__ import annotations

import crescent
import hikari

from .config import CONFIG


INTENTS = (
    hikari.Intents.GUILDS
    | hikari.Intents.GUILD_VOICE_STATES
)


class Bot(crescent.Bot):
    def __init__(self) -> None:
        super().__init__(
            token=CONFIG.token,
            intents=INTENTS,
        )

    async def join(self, channel: hikari.GuildVoiceChannel) -> None:
        await self.voice.connect_to(channel.guild_id, channel)
