from __future__ import annotations

from typing import TYPE_CHECKING, cast

import crescent

from melody.exceptions import MelodyErr

from .checks import guild_only, vc_match

if TYPE_CHECKING:
    from melody.bot import Bot


plugin = crescent.Plugin("music")


@plugin.include
@crescent.catch(MelodyErr)
async def on_err(err: MelodyErr, ctx: crescent.Context) -> None:
    await ctx.respond(err.msg, ephemeral=True)


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="play")
class PlaySong:
    url = crescent.option(str, "The URL of the song to play.")

    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        vc_state = bot.cache.get_voice_state(ctx.guild_id, ctx.user.id)
        if vc_state is None or vc_state.channel_id is None:
            raise MelodyErr("You're not in a voice channel.")
        ret = await bot.join_vc(ctx.guild_id, vc_state.channel_id)
        if ret is True:
            await ctx.respond(f"Connected to <#{vc_state.channel_id}>.")
        else:
            await ctx.defer()

        await bot.play_url(ctx.guild_id, self.url)
        await ctx.respond("Song added to queue.")


@plugin.include
@crescent.hook(guild_only)
@crescent.hook(vc_match)
@crescent.command(name="leave")
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
@crescent.command(name="pause")
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
@crescent.command(name="resume")
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
@crescent.command(name="skip")
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
@crescent.command(name="queue")
class ShowQueue:
    async def callback(self, ctx: crescent.Context) -> None:
        bot = cast("Bot", ctx.app)
        assert ctx.guild_id is not None

        player = bot.players.get(ctx.guild_id)
        if player is None:
            raise MelodyErr("The queue is empty!")

        np = player.queue.track_handle

        upcoming_titles = []
        for track in player.queue:
            upcoming_titles.append((await track.metadata()).title)

        if np is None and not len(upcoming_titles):
            raise MelodyErr("The queue is empty!")
        await ctx.respond(
            (
                f"Now playing: **{np.metadata.title}**\n"
                if np is not None
                else "Nothing playing right now.\n"
            )
            + (
                "Upcoming:\n-" + "\n-".join(upcoming_titles)
                if upcoming_titles
                else "Nothing upcoming."
            )
        )
