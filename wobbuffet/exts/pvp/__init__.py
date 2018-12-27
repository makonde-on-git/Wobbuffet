"""This cog contains features relating to Pokemon Go PvP."""

from .pvp_cog import PvP


def setup(bot):
    bot.add_cog(PvP(bot))
    bot.config.command_categories['PvP'] = {
        "index": "66", "description": "PvP related commands."
    }
