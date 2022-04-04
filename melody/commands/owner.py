from __future__ import annotations

from typing import TYPE_CHECKING, cast

import crescent

from .checks import owner_only

if TYPE_CHECKING:
    from melody.bot import Bot

plugin = crescent.Plugin("owner")


@plugin.include
@crescent.hook(owner_only)
@crescent.command(name="shell", description="Execute a shell command.")
class Shell:
    command = crescent.option(str, "The command to execute.")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.defer(True)
        bot = cast("Bot", ctx.app)
        out = bot.run_shell(self.command)
        await ctx.respond(out or "No response.")


@plugin.include
@crescent.hook(owner_only)
@crescent.command(name="exec", description="Execute a Python command.")
class Exec:
    command = crescent.option(str, "The command to execute.")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.defer(True)
        bot = cast("Bot", ctx.app)
        out, ret = await bot.exec_code(self.command, {"bot": bot})
        await ctx.respond(f"Output: ```\n{out}\n```\n\nReturn: {ret}")


@plugin.include
@crescent.hook(owner_only)
@crescent.command(name="reload", description="Reload a plugin.")
class Reload:
    plugin = crescent.option(str, "The plugin to reload.")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.defer(True)
        bot = cast("Bot", ctx.app)
        bot.plugins.load(self.plugin, refresh=True)
        await bot._command_handler.register_commands()
        await ctx.respond(f"Reloaded {self.plugin}.")
