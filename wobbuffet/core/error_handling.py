import traceback
import asyncio

from inspect import signature, getfullargspec

import discord
from discord.ext import commands

from wobbuffet import errors


async def delete_error(message, error):
    try:
        await message.delete()
    except (discord.errors.Forbidden, discord.errors.HTTPException):
        pass
    try:
        await error.delete()
    except (discord.errors.Forbidden, discord.errors.HTTPException):
        pass


def missing_arg_msg(ctx):
    prefix = ctx.prefix.replace(ctx.bot.user.mention, '@' + ctx.bot.user.name)
    command = ctx.invoked_with
    callback = ctx.command.callback
    sig = list(signature(callback).parameters.keys())
    args, varargs, __, defaults, __, kwonlydefaults, __ = getfullargspec(callback)
    if defaults:
        rq_args = args[:(- len(defaults))]
    else:
        rq_args = args
    if varargs:
        if varargs != 'args':
            rq_args.append(varargs)
    arg_num = len(ctx.args) - 1
    sig.remove('ctx')
    args_missing = sig[arg_num:]
    msg = _("Usage: {prefix}{command}").format(prefix=prefix, command=command)
    for a in sig:
        if kwonlydefaults:
            if a in kwonlydefaults.keys():
                msg += ' [{0}]'.format(a)
                continue
        if a in args_missing:
            msg += ' **<{0}>**'.format(a)
        else:
            msg += ' <{0}>'.format(a)
    return msg


class ErrorHandler:

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.bot.send_cmd_help(
                ctx, title='Missing Arguments', msg_type='error')

        elif isinstance(error, commands.BadArgument):
            await ctx.bot.send_cmd_help(
                ctx, title=f'Bad Argument - {error}', msg_type='error')

        elif isinstance(error, errors.MissingSubcommand):
            await ctx.bot.send_cmd_help(
                ctx, title=f'Missing Subcommand - {error}', msg_type='error')

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("That command is disabled.")

        elif isinstance(error, commands.CommandInvokeError):
            ctx.bot.logger.exception(
                "Exception in command '{}'".format(ctx.command.qualified_name),
                exc_info=error.original)
            message = ("Error in command '{}'. Check your console or "
                       "logs for details."
                       "".format(ctx.command.qualified_name))
            exception_log = ("Exception in command '{}'\n"
                             "".format(ctx.command.qualified_name))
            exception_log += "".join(traceback.format_exception(
                type(error), error, error.__traceback__))
            ctx.bot._last_exception = exception_log
            await ctx.send(message)

        elif isinstance(error, commands.CommandNotFound):
            error = await ctx.send("Command not found.")
            await asyncio.sleep(10)
            await delete_error(ctx.message, error)

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("That command is not available in DMs.")

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown. "
                           "Try again in {:.2f}s"
                           "".format(error.retry_after))


def setup(bot):
    bot.add_cog(ErrorHandler())
