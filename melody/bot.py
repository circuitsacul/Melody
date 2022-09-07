from __future__ import annotations

import asyncio
import traceback
from asyncio import Lock
from contextlib import asynccontextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from textwrap import indent
from typing import Any, AsyncIterator

import crescent
import hikari
from songbird import Queue, Source, get_playlist, ytdl
from songbird.hikari import Voicebox
from songbird.playlist import YoutubeVideo

from melody.exceptions import MelodyErr

from .config import CONFIG

INTENTS = hikari.Intents.GUILDS | hikari.Intents.GUILD_VOICE_STATES


@dataclass
class Player:
    voicebox: Voicebox
    queue: Queue


class Bot(crescent.Bot):
    def __init__(self) -> None:
        super().__init__(
            token=CONFIG.token, intents=INTENTS, default_guild=CONFIG.guild
        )

        self.players: dict[int, Player] = {}
        self.locks: dict[int, Lock] = {}
        self.plugins.load_folder("melody.commands")

    @property
    def me(self) -> hikari.OwnUser:
        me = self.get_me()
        assert me is not None
        return me

    async def exec_code(
        self, code: str, glbls: dict[str, Any] | None = None
    ) -> tuple[str, Any]:
        code = indent(code, "    ")
        code = (
            f"async def _async_internal_exec_func_wrap():\n{code}\n\nresult="
            "_async_internal_exec_func_wrap()"
        )

        lcls: dict[str, Any] = {}
        f = StringIO()
        with redirect_stderr(f):
            with redirect_stdout(f):
                try:
                    exec(code, glbls, lcls)
                    result = await lcls["result"]
                except Exception:
                    return traceback.format_exc(), None

        return f.getvalue(), result

    @asynccontextmanager
    async def lock(self, guild: int) -> AsyncIterator[None]:
        lock = self.locks.get(guild, Lock())
        try:
            await lock.acquire()
            yield
        finally:
            lock.release()
            # TODO: use a weakref for locks

    async def verify_vc_loop(self) -> None:
        while True:
            for guild in list(self.players.keys()):
                await self.verify_vc(guild)
                await asyncio.sleep(0.5)
            await asyncio.sleep(60)

    async def verify_vc(self, guild: int) -> None:
        async with self.lock(guild):
            voice = self.players.get(guild)
            if not voice:
                return
            if not voice.voicebox.is_alive:
                await self.leave_vc(guild)
                return
            if not self.voice.connections.get(hikari.Snowflake(guild)):
                await self.leave_vc(guild)
                return
            if not self.cache.get_voice_state(guild, self.me.id):
                await self.leave_vc(guild)
                return
            channel = self.cache.get_guild_channel(voice.voicebox.channel_id)
            if channel is None:
                await self.leave_vc(guild)
                return
            connected = self.cache.get_voice_states_view_for_channel(
                channel.guild_id, channel
            )
            if len(connected) == 1:  # Bot is the only one in the channel
                await self.leave_vc(guild)

    async def join_vc(self, guild: int, channel: int) -> bool:
        await self.verify_vc(guild)
        async with self.lock(guild):
            if guild in self.players:
                return False
            voice = await Voicebox.connect(
                self, hikari.Snowflake(guild), hikari.Snowflake(channel)
            )
            self.players[guild] = Player(voice, Queue(voice.driver))
        return True

    async def leave_vc(self, guild: int) -> bool:
        voice = self.players.pop(guild, None)
        if not voice:
            return False
        try:
            await voice.voicebox.leave()
        except Exception:
            pass
        try:
            vc = self.voice.connections.get(hikari.Snowflake(guild))
            if vc:
                await vc.disconnect()
        except Exception:
            pass

        return True

    async def play_url(
        self, guild: int, url: str, is_playlist: bool = False
    ) -> Source | list[YoutubeVideo]:
        async with self.lock(guild):
            voice = self.players.get(guild)
            if not voice:
                raise MelodyErr("I am not in a voice channel!")
            if "playlist" in url or is_playlist:
                try:
                    sources = await get_playlist(url)
                except Exception:
                    pass
                else:
                    voice.queue.extend(sources)
                    return sources
            if not is_playlist:
                try:
                    source = await ytdl(url)
                except Exception:
                    raise MelodyErr("Invalid YouTube URL!")
                else:
                    voice.queue.append(source)
                    return source
            raise MelodyErr("URL is not a playlist!")
