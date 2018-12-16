#!/usr/bin/python3
"""Wobbuffet - A Discord helper bot for Pokemon Go communities, dedicated to PvP.
Wobbuffet is a Discord bot written in Python 3.6 using version 1.0.0a (rewrite)
of the discord.py library. It assists with the organisation of local
PvP for Pokemon Go Discord servers and their members.

Big (really big, like huge) part of the code is based on Meowth v3 bot by FoglyOgly
and Scragly. Big kudos for awesome work they do!
"""

__version__ = "0.0.1"

__author__ = "Makonde"
__credits__ = ["Makonde", "FoglyOgly", "Scragly"]
__license__ = "GNU General Public License v3.0"
__maintainer__ = "Makonde"
__status__ = "Production"

from .core import bot, checks, Cog, command, context, errors, group
from .core.data_manager import dbi, schema, sqltypes
