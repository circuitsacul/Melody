from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, cast

import crescent

from .checks import owner_only

if TYPE_CHECKING:
    from melody.bot import Bot

plugin = crescent.Plugin()


@plugin.include
@crescent.hook(owner_only)
@crescent.command(name="shell", description="Execute a shell command.")
class Shell:
    command = crescent.option(str, "The command to execute.")

    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.defer(True)
        out, err = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()
        await ctx.respond(
            "```\n"
            + ((out.decode("utf-8") + err.decode("utf-8")) or "No output.")
            + "```"
        )


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
