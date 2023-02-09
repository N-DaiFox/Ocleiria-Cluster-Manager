from discord.ext import commands
import discord
import aiohttp


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.appId = 727114852245569545
        self.cfg = bot.cfg
        self.token = self.cfg.token
        self.authheader = {"Authorisation": f"Bot {self.token}"}

    async def cog_before_invoke(self, ctx):
        # if we have no http pool
        if getattr(self, "httpSession", None) == None:
            # create it
            self.httpSession = aiohttp.ClientSession()

    @commands.command(slash_command=False)
    async def testslash(self, ctx):
        # get local slash commands
        resp = await self.httpSession.get(
            f"https://discord.com/api/v8/applications/{self.appId}/guilds/{ctx.guild.id}/commands",
            headers=self.authheader,
        )
        # await ctx.send(resp)
        # if 200 http code
        if resp.status == 200:
            # construct embed
            embed = discord.Embed()
            embed.title = "Tout est OK!"
            embed.description = (
                "Vous avez tout configuré pour utiliser les nouvelles commandes slash."
            )
            embed.colour = discord.Colour.green()
        # if 403 we don't have new OAuth2 scope
        elif resp.status == 403:
            # construct error with reinvite link
            embed = discord.Embed()
            embed.title = "Tu dois réinviter le bot!"
            embed.add_field(
                name="Discord nécessite une réinvitation pour certains serveurs plus anciens.",
                value="Vous **devriez** réinviter le bot avec [ce link]!",
            )
            embed.set_footer(text="Aucune donnée ne sera perdue lors de la réinvitation du bot!")
            embed.colour = discord.Colour.red()
        # something bad happened
        else:
            # construct error message
            embed = discord.Embed()
            embed.title = "Oups, quelque chose s'est mal passé de notre côté."
            embed.description = (
                "Merci de réessayer dans quelques minutes Signalez ce problème s'il persiste."
            )
            embed.colour = discord.Colour.red()
        # get permissions for current user
        perms = ctx.channel.permissions_for(ctx.author)
        # if the user can use slash commands
        if perms.use_slash_commands:
            embed2 = discord.Embed()
            embed2.title = "Vous pouvez exécuter des commandes slash!"
            embed2.description = "J'ai vérifié vos autorisations et vous pouvez exécuter la commande slash dans le salon actuel."
            embed2.colour = discord.Colour.green()
        else:
            embed2 = discord.Embed()
            embed2.title = "Vous ** ne pouvez pas ** exécuter des commandes slash!"
            embed2.description = "J'ai vérifié vos permissions et vous **ne pouvez** pas exécuter la commande slash dans le canal actuel. Veuillez vérifier vos autorisations. Vous devriez activer [Utiliser les commandes de l'application](https://media.discordapp.net/attachments/1069926548058165278/1073038632820146248/image.png) autorisation."
            embed2.colour = discord.Colour.red()
        await ctx.send(embeds=[embed, embed2])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Slash(bot))
