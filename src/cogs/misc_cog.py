from cogs.utils.helpers import *  # all our helpers
import cogs.utils.classes as c  # all our classes
import discord  # main discord lib
from discord.ext import commands
from discord.ext import tasks
import cogs.utils.menus as m

# import /server command module (see server_cmd.py)
# import server_cmd as server
import json
import config
import datetime
import psutil
from psutil._common import bytes2human
import statistics
import time
import arrow


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.t = c.Translation()
        # start warnings reset task
        self.reset_warnings.start()

    @tasks.loop(hours=24.0)
    async def reset_warnings(self):
        self.bot.deprecation_warnings = {}

    async def selectServersByIds(self, ids):
        # empty statement
        statement = "SELECT * FROM servers WHERE Id IN ({})"
        # construct part of the query
        param = ", ".join([str(i) for i in ids])
        print(statement.format(param))
        # return result
        return await makeAsyncRequest(statement.format(param))

    def noServers(self, ctx):
        # create error embed
        embed = discord.Embed()
        # paint it
        embed.color = randomColor()
        # add title
        embed.title = "On dirait que vous n'avez pas de serveurs ajoutés !"
        # and description
        embed.description = (
            f"Vous pouvez ajouter n'importe quel serveur Steam en utilisant la commande `{ctx.prefix}server add`"
        )
        # and return
        return embed

    async def listServers(self, ctx):
        # select settings of the guild
        settings = await makeAsyncRequest(
            "SELECT * FROM settings WHERE GuildId=%s", (ctx.guild.id,)
        )
        # if no settings found
        if settings.__len__() <= 0 or settings[0][3] == None:
            # send no servers embed
            return self.noServers(ctx)
        # get ids of added servers in this guild
        serversIds = json.loads(settings[0][3])
        # if we have no servers added
        if serversIds.__len__() <= 0:
            # return no servers embed
            return self.noServers(ctx)
        # select servers by ids
        servers = await self.selectServersByIds(serversIds)
        # create embed
        embed = discord.Embed()
        # paint it
        embed.color = randomColor()
        # set title
        embed.title = "Liste des serveurs:"
        # index of the first server
        i = 1
        # for each server
        for server in servers:
            # load server object
            serverObj = c.ARKServer.fromJSON(server[4])
            # load more info about server
            info = json.loads(server[8])
            # create field name
            fieldName = f"{i}. {await stripVersion(serverObj)}"
            # if server is online set status to online string
            # else to offline string
            status = (
                ":green_circle: En Ligne" if server[6] == 1 else ":red_circle: Hors Ligne"
            )
            # create field value
            fieldValue = f'[{server[1]}]({info.get("battleUrl","")}) {status}'
            # add field to embed
            embed.add_field(name=fieldName, value=fieldValue)
            # increment index
            i += 1
        # return embed
        return embed

    async def listNotifications(self, ctx):
        # select all notifications for current guild
        # (won't work with old table format)
        notifications = await makeAsyncRequest(
            "SELECT * FROM notifications WHERE GuildId = %s", (ctx.guild.id,)
        )
        # if there are no notifications
        if notifications.__len__() <= 0:
            # return nothing
            return None
        # create embed
        embed = discord.Embed()
        # paint it
        embed.color = randomColor()
        # add title
        embed.title = "Liste des notifications:"
        # notification index
        i = 1
        # for each record in db
        for record in notifications:
            # load server ids
            serverIds = json.loads(record[4])
            # if no servers in record
            if serverIds.__len__() <= 0:
                # skip it
                continue
            # load server records
            servers = await self.selectServersByIds(serverIds)
            # for each server
            for server in servers:
                # make server object from record
                server = c.ARKServer.fromJSON(server[4])
                # make name and value
                name = f"{i}. Notification pour `{await stripVersion(server)}`"
                value = f"Sur <#{record[1]}>"
                # and add field
                embed.add_field(name=name, value=value)
                i += 1
        # if no fields were added
        if i <= 1:
            return None
        # else return embed
        return embed

    async def listAutoMessages(self, ctx):
        # select all messages for this guild
        records = await makeAsyncRequest(
            "SELECT * FROM automessages WHERE DiscordGuildId = %s", (ctx.guild.id,)
        )
        # if no records found
        if records.__len__() <= 0:
            # return nothing
            return None
        # create embed
        embed = discord.Embed()
        # paint it
        embed.color = randomColor()
        # add title
        embed.title = "Liste des messages auto :"
        # get ids of all servers in records
        serversIds = [record[3] for record in records]
        # get servers from those ids
        servers = await self.selectServersByIds(serversIds)
        # auto message index
        index = 1
        # for each record
        for i, record in enumerate(records):
            # create server object from server record
            server = c.ARKServer.fromJSON(servers[i][4])
            # create link to message from auto message record
            msgLink = f"https://discordapp.com/channels/{ctx.guild.id}/{record[1]}/{record[2]}"
            # create name and value for field
            name = f"{index}. Message pour `{await stripVersion(server)}`"
            value = f"[Message]({msgLink}) sur <#{record[1]}>"
            # add field
            embed.add_field(name=name, value=value)
            index += 1
        # return embed
        return embed

    def getUptime(self):
        # get current process
        proc = psutil.Process()
        # get process creation date
        # (in float UNIX timestamp)
        creationTime = arrow.get(proc.create_time())
        # get current time in UNIX timestamp
        currentTime = arrow.utcnow()
        # get uptime
        uptime = currentTime - creationTime
        # get components of datetime.timedelta
        # where is .format() python ?!
        days = uptime.days
        seconds = uptime.seconds % 60
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds // 60) % 60
        # if less then 1 hour
        if hours == 0:
            # return just minutes + seconds
            return f"{minutes:01}:{seconds:01}"
        # if less than 1 day
        elif days == 0:
            # return just hours + minutes + seconds
            return f"{hours:01}:{minutes:01}:{seconds:01}"
        else:
            # return full string
            return f"{days} jours {hours:01}:{minutes:01}:{seconds:01}"

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command(brief="Listez tout ce que vous pouvez créer dans ce bot")
    async def list(self, ctx):
        # TODO re-do this to use multiple embeds in one message (need d.py 2.0 for that)
        # IDEA maybe you can select what you are trying to list ? like :
        # /list servers, /list notifications
        # make all coroutines
        coroutines = [
            self.listServers(ctx),
            self.listNotifications(ctx),
            self.listAutoMessages(ctx),
        ]
        # run them concurrently
        embeds = await asyncio.gather(*coroutines)
        # remove none's
        embeds = list(filter(None, embeds))
        # await ctx.send(embeds)
        # send them
        await ctx.send(embeds=embeds)

    @commands.bot_has_permissions(
        add_reactions=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
        external_emojis=True,
    )
    @commands.command(brief="Obtenir des informations sur ce bot")
    async def info(self, ctx):
        # get how many servers we have in DB
        count = await makeAsyncRequest("SELECT COUNT(Id) FROM servers")
        # get object to get time
        time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        # get total and used memory in the system
        RAM = f"{bytes2human(psutil.virtual_memory().used)}/{bytes2human(psutil.virtual_memory().total)}"
        # get bot's role
        role = ctx.me.top_role.mention if ctx.me.top_role != "@everyone" else "No role"
        # create embed
        embed = discord.Embed(
            title=f"Infos sur {self.bot.user.name}",
            timestamp=time.utcnow(),
            color=randomColor(),
        )
        # set footer
        embed.set_footer(
            text=f"Demandé par {ctx.author.name} • Bot {self.cfg.version} • Temps de fonctionnement: {self.getUptime()} ",
            icon_url=ctx.author.display_avatar,
        )
        # add fields
        embed.add_field(
            name="<:Link:739476980004814898> Notre Site",
            value="[Ici!](https://ocleiria.fr)",
            inline=True,
        )
        embed.add_field(
            name="<:Github:739476979631521886> Liste Mod",
            value="[Here!](https://steamcommunity.com/sharedfiles/filedetails/?id=2910181822)",
            inline=True,
        )
        embed.add_field(
            name="<:Discord:739476979782254633> Serveur Discord",
            value="[Here!](https://ocleiria.fr/discord)",
            inline=True,
        )
        embed.add_field(
            name="<:DB:739476980075986976> Serveurs dans la base de données",
            value=f"{count[0][0]}",
            inline=True,
        )
        embed.add_field(name="<:RAM:739476925852155914> RAM", value=RAM, inline=True)
        embed.add_field(
            name="<:Bot:748958111456296961> Version",
            value=self.cfg.version,
            inline=True,
        )
        embed.add_field(
            name=":ping_pong: Ping",
            value=f"{int(self.bot.latency * 1000)} ms",
            inline=True,
        )
        embed.add_field(
            name="<:me:739473644874367007> Créateur", value=f"DaiFox", inline=True
        )
        embed.add_field(
            name="<:Discord:739476979782254633> Seulement sur",
            value=f"Le serveur Ocleiria",
            inline=True,
        )
        embed.add_field(
            name="<:Role:739476980076118046> Rôle sur ce serveur",
            value=role,
            inline=True,
        )
        embed.add_field(
            name=":grey_exclamation: Préfixe actuel",
            value=f"{ctx.prefix}",
            inline=True,
        )
        embed.add_field(
            name="<:Cpu:739492057990693005> Utilisation actuelle du CPU",
            value=f"{round(statistics.mean(psutil.getloadavg()),1)}",
            inline=True,
        )
        # guild 1 is special value
        message = await makeAsyncRequest("SELECT * FROM settings WHERE GuildId=1")
        if message.__len__() <= 0:
            message = "Merci d'etre aussi nombreux tous les jours.\nEn route vers les 200 Membres."
        else:
            message = message[0][4]
        embed.add_field(name="Message du créateur", value=message)
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(send_messages=True)
    @commands.command(brief="Obtenir des informations à donner à l'équipe d'assistance")
    async def ticketinfo(self, ctx):
        text = ""
        text += f"Votre identifiant de guilde est : {ctx.guild.id}\n"
        permissions = ctx.channel.permissions_for(ctx.guild.me)
        text += f"Mes permissions actuelles dans le canal actuel sont : {permissions.value}\n"
        text += f"Est-ce que l'utilisation des commandes slash est.. : {True if ctx.interaction is not None else False}"
        await ctx.send(discord.utils.escape_mentions(text))


def setup(bot: commands.Bot) -> None:
    cog = MiscCommands(bot)
    bot.add_cog(cog)
