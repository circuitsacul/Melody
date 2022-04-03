from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, cast

import crescent
import hikari

from melody.config import CONFIG
from melody.exceptions import MelodyErr

if TYPE_CHECKING:
    from melody.bot import Bot


async def owner_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if ctx.user.id not in CONFIG.owners:
        msg = MelodyErr("Only owners can use this command.")
        await ctx.respond(msg.msg, ephemeral=True)
        return crescent.HookResult(True)

    return None


async def guild_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if not ctx.guild_id:
        msg = MelodyErr("This command can only be used inside servers.")
        await ctx.respond(msg.msg, ephemeral=True)
        return crescent.HookResult(True)

    return None


async def vc_match(ctx: crescent.Context) -> crescent.HookResult | None:
    await guild_only(ctx)
    bot = cast("Bot", ctx.app)
    assert ctx.guild_id is not None
    assert ctx.member is not None

    vc_state = bot.cache.get_voice_state(ctx.guild_id, ctx.member.id)
    await bot.verify_vc(ctx.guild_id)
    player = bot.players.get(ctx.guild_id)
    if vc_state is None:
        msg = MelodyErr("You're not in a voice channel.")
        await ctx.respond(msg.msg, ephemeral=True)
        return crescent.HookResult(True)
    elif player is None:
        return None
    elif vc_state.channel_id != player.voicebox.channel_id:
        msg = MelodyErr("You're not in the same voice channel as me.")
        await ctx.respond(msg.msg, ephemeral=True)
        return crescent.HookResult(True)

    return None


def has_guild_perms(
    perms: hikari.Permissions,
) -> Callable[[crescent.Context], Awaitable[crescent.HookResult | None]]:
    async def check(ctx: crescent.Context) -> crescent.HookResult | None:
        await guild_only(ctx)
        assert ctx.guild_id is not None
        assert ctx.member is not None
        assert isinstance(member := ctx.member, hikari.InteractionMember)

        guild = ctx.app.cache.get_guild(ctx.guild_id)
        assert guild is not None

        if perms not in member.permissions:
            msg = MelodyErr("You don't have permission to use this command.")
            await ctx.respond(msg.msg, ephemeral=True)
            return crescent.HookResult(True)

        return None

    return check
