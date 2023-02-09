import cogs.utils.classes as c  # our classes
from cogs.utils.helpers import *  # our helpers
import config  # config
import discord  # main discord libary
from discord.ext import commands  # import commands extension
from discord.ext import tasks
import datetime


class Charcoal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate = 1
        self.cfg = config.Config()
        pass

    def calculate(self, charcoal: int, campCount: int = 1):
        import math

        self.neededWood = charcoal

        self.woodPerForge = charcoal // campCount

        self.cookTime = self.neededWood // 30

        self.cookTimeMin = str(int(self.cookTime // 60)).zfill(2)
        self.cookTimeSec = str(int(self.cookTime - (int(self.cookTimeMin) * 60))).zfill(
            2
        )
        self.cookTimeHor = str(int(self.cookTime // 3600)).zfill(2)

    async def sendEmbed(self, ctx, title, name, value):
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        emb = discord.Embed(title=title, timestamp=time.utcnow())
        emb.set_footer(
            text=f"Demandé par {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ",
            icon_url=ctx.author.display_avatar,
        )
        emb.add_field(name=name, value=value)
        ctx.send(embed=emb)
        return

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command(slash_command=False)
    async def charcoal(self, ctx, ammount: int = None, camps: int = 1):
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        if ammount == None:
            await self.sendEmbed(
                ctx,
                "Oups!",
                "Vous ne pouvez pas utiliser 0 ou des nombres négatifs pour `ammount` paramètre!",
                f"Vous avez besoin de charbon de bois et non {ammount}!",
            )
            return
        if camps <= 0:
            await self.sendEmbed(
                ctx,
                "Oups!",
                "Vous ne pouvez pas utiliser 0 ou des nombres négatifs pour `camps` paramètre!",
                "Ne le faites pas. Vous ne pouvez pas faire du charbon de bois sans feu de camps n'est-ce pas ?",
            )
            return
        self.calculate(ammount, camps)
        emb = discord.Embed(title="Charbon de bois", timestamp=time.utcnow())
        emb.set_footer(
            text=f"Demandé par {ctx.author.name} • Bot {self.cfg.version} • GPLv3 ",
            icon_url=ctx.author.display_avatar,
        )
        if camps == 1:
            emb.add_field(
                name="Temps :",
                value=f"{self.cookTimeHor}:{self.cookTimeMin}:{self.cookTimeSec}",
                inline=True,
            )
            emb.add_field(name="Bois:", value=self.neededWood, inline=False)
            emb.set_thumbnail(
                url="https://static.wikia.nocookie.net/arksurvivalevolved_gamepedia/images/4/4f/Charcoal.png"
            )
            await ctx.send(embed=emb)
            return
        else:
            emb.add_field(
                name="Temps :",
                value=f"{self.cookTimeHor}:{self.cookTimeMin}:{self.cookTimeSec}",
                inline=False,
            )
            emb.add_field(name="Bois total :", value=self.totalWood, inline=False)
            emb.add_field(name="Bois (per camp):", value=self.woodPerCamp, inline=False)
            emb.set_thumbnail(
                url="https://static.wikia.nocookie.net/arksurvivalevolved_gamepedia/images/4/4f/Charcoal.png"
            )
            await ctx.send(embed=emb)
            return


def setup(bot: commands.Bot) -> None:
    pass
    # bot.add_cog(Charcoal(bot))
