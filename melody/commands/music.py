from __future__ import annotations

import datetime
from inspect import isawaitable
from typing import TYPE_CHECKING, cast

import crescent
import hikari

from melody.config import CONFIG
from melody.exceptions import MelodyErr

from .checks import guild_only, vc_match

if TYPE_CHECKING:
    from melody.bot import Bot


plugin = crescent.Plugin("music")


def song_infostr(meta) -> str:
    length = str(datetime.timedelta(seconds=meta.duration))
    return f"[{meta.title}](<{meta.source_url}>) ({length})"


@plugin.include
@crescent.catch_command(MelodyErr)
async def on_err(err: MelodyErr, ctx: crescent.Context) -> None:
    await ctx.respond(err.msg, ephemeral=True)


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="play", description="Play a song from URL.")
class PlaySong:
    url = crescent.option(str, "The URL of the song to play.")
    is_playlist = crescent.option(
        bool,
        "Whether the URL is a playlist.",
        default=False,
        name="is-playlist",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        await ctx.defer()

        vc_state = bot.cache.get_voice_state(ctx.guild_id, ctx.user.id)
        if vc_state is None or vc_state.channel_id is None:
            raise MelodyErr("You're not in a voice channel.")
        await bot.join_vc(ctx.guild_id, vc_state.channel_id)

        source = await bot.play_url(
            ctx.guild_id, self.url, is_playlist=self.is_playlist
        )
        if isinstance(source, list):
            await ctx.respond(
                "Added {} songs to queue.".format(len(source)), ephemeral=True
            )
        else:
            await ctx.respond(
                "Added to queue: " + song_infostr(await source.metadata())
            )


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(
    name="leave", description="Clear the queue and leave the voice channel."
)
class Leave:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        ret = await bot.leave_vc(ctx.guild_id)
        if ret:
            await ctx.respond("Disconnected from voice channel.")
        else:
            await ctx.respond("I am not in a voice channel.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(
    name="volume", description="Set the volume of the current song."
)
class SetVolume:
    volume = crescent.option(
        int,
        "The volume to set the player to.",
        min_value=0,
        max_value=100,
        default=100,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        await bot.verify_vc(ctx.guild_id)
        player = bot.players.get(ctx.guild_id)
        if player is None:
            raise MelodyErr("I am not in a voice channel.")
        if player.queue.track_handle is None:
            raise MelodyErr("There's no song playing.")
        player.queue.track_handle.set_volume(self.volume / 100)
        await ctx.respond(f"Volume set to {self.volume}%.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="pause", description="Pause the current song.")
class PauseQueue:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if not player or not player.queue.track_handle:
            raise MelodyErr("There's no song playing.")

        player.queue.track_handle.pause()
        await ctx.respond("Paused.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="resume", description="Resume the current song.")
class ResumeQueue:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if not player or not player.queue.track_handle:
            raise MelodyErr("There's no song playing.")

        player.queue.track_handle.play()
        await ctx.respond("Resumed.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="skip", description="Skip the current song.")
class SkipTrack:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if not player or not player.queue.track_handle:
            raise MelodyErr("There's no song playing.")

        player.queue.skip()
        await ctx.respond("Skipped.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="seek", description="Seek to a specific time.")
class SeekTrack:
    seconds = crescent.option(int, "The time to seek to.", min_value=0)

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if not player or not player.queue.track_handle:
            raise MelodyErr("There's no song playing.")

        if not player.queue.track_handle.is_seekable:
            raise MelodyErr("This song is not seekable.")

        player.queue.track_handle.seek_time(self.seconds)
        await ctx.respond(f"Set position to {self.seconds}.")


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="queue", description="Show the currently playing and upcoming songs."
)
class ShowQueue:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if player is None:
            raise MelodyErr("The queue is empty!")

        np = player.queue.track_handle

        current_len = 0
        upcoming: list[str] = []
        for x, track in enumerate(player.queue):
            meta = track.metadata
            if hasattr(meta, "__call__"):
                meta = meta()
            if isawaitable(meta):
                meta = await meta
            infostr = f"{x}. {song_infostr(meta)}"
            if (current_len + len(infostr)) + 2 * len(upcoming) > 2000:
                upcoming.append("And others...")
                break
            current_len += len(infostr)
            upcoming.append(infostr)

        if np is None and not len(upcoming):
            raise MelodyErr("The queue is empty!")
        embed = hikari.Embed(
            title="Queue",
            color=CONFIG.theme,
            description=(
                (
                    f"Now playing: {song_infostr(np.metadata)}"
                    if np
                    else "Nothing playing right now."
                )
                + (
                    "\n\nUpcoming:\n{}".format("\n".join(upcoming))
                    if upcoming
                    else ""
                )
            ),
        )
        await ctx.respond(embed=embed)


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="nowplaying", description="Show the currently playing song."
)
class ShowNowPlaying:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if player is None:
            raise MelodyErr("There is no song playing!")

        np = player.queue.track_handle

        if np is None:
            raise MelodyErr("There is no song playing!")

        state = await np.get_info()
        current = str(datetime.timedelta(seconds=int(state.position)))
        total = str(datetime.timedelta(seconds=int(np.metadata.duration or 0)))

        embed = (
            hikari.Embed(
                title=np.metadata.title,
                color=CONFIG.theme,
                description=(
                    f"Duration: {current}/{total}\n"
                    f"Volume: {int(state.volume*100)}%"
                ),
                url=np.metadata.source_url,
            )
            .set_footer(text=np.metadata.artist or "Unkown Artist")
            .set_thumbnail(np.metadata.thumbnail)
        )
        await ctx.respond(embed=embed)
