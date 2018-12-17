import asyncio

from wobbuffet import Cog, command


class PvP(Cog):

    @command()
    async def won_vs(self, ctx, *, player):
        """Set your Pokemon Go team."""

        to_delete = [await ctx.send("command won_vs: {}".format(player))]
        to_delete.append(await ctx.send("channel: {}".format(ctx.channel.id)))
        to_delete.append(await ctx.send("channel name: {}".format(ctx.bot.get_channel(ctx.channel.id))))
        to_delete.append(await ctx.send("has mentions: {}".format(len(ctx.message.mentions))))
        if len(ctx.message.mentions):
            to_delete.append(await ctx.send("id: {}".format(ctx.message.mentions[0].id)))
            to_delete.append(await ctx.send("mention: {}".format(ctx.message.mentions[0].mention)))
        to_delete.append(ctx.message)
        await asyncio.sleep(3)
        await ctx.channel.delete_messages(to_delete)
