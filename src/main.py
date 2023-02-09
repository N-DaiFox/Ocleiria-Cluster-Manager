# from charcoal import Charcoal
# import cogs.utils.classes as c  # our classes
from cogs.utils.helpers import *  # our helpers
import config  # config
import discord  # main discord library
from discord.ext import commands  # import commands extension

# from server_cmd import *  # !server command
import json  # json module
import traceback  # traceback
import time  # time
from datetime import datetime
from discord import permissions
from discord.ext.commands import has_permissions, CheckFailure
from pathlib import Path

# classes.py - just classes for data shareing and processing
# config.py - main bot config
# commands.py - all commands live here
# helpers.py - helper functions (like work with DB)

debug = Debuger("main")  # create debugger (see helpers.py)
conf = config.Config()  # load config
# set custom status for bot (sadly it isn't possible to put buttons like in user's profiles)
game = discord.Game("ping moi pour obtenir le préfixe")
intents = discord.Intents(messages=True, guilds=True, reactions=True)
# create auto sharded bot with default prefix and no help command
bot = commands.AutoShardedBot(
    intents=intents,
    command_prefix=get_prefix,
    help_command=None,
    activity=game,
    slash_commands=True,
    slash_command_guilds=[349178138258833418],
    strip_after_prefix=True,
)
bot.cfg = conf
# key: guild id
# value: how many times this guild seen deprecation warning
bot.deprecation_warnings = {}
debug.debug("Inited DB and Bot!")  # debug into console !
t = c.Translation()  # load default english translation

# if conf.debug is True asyncio will output additional debug info into logs
bot.loop.set_debug(conf.debug)

# setup function
def setup():
    print("Commencé à charger les cogs")
    # search for cogs
    cogs = [p.stem for p in Path(".").glob("./src/cogs/*.py")]
    print(cogs)
    for cog in cogs:
        print(f"cogs.{cog}")
        bot.load_extension(f"cogs.{cog}")
        print(f"{cog} cog chargé")
    # load jishaku
    bot.load_extension("jishaku")
    # hide it's command
    bot.get_command("jsk").hidden = True
    print("Fonction de configuration terminée")


# ~~~~~~~~~~~~~~~~~~~~~
#       COMMANDS
# ~~~~~~~~~~~~~~~~~~~~~

# !prefix command
# default permissions check
@commands.bot_has_permissions(
    add_reactions=True,
    read_messages=True,
    send_messages=True,
    manage_messages=True,
    external_emojis=True,
)
@bot.command(brief="Change prefix lol", slash_command=False)
async def prefix(ctx, prefix: str = commands.Option(None, description="Prefix")):
    if not prefix:  # if no prefix
        # send current prefix and return
        await ctx.send(t.l["curr_prefix"].format(ctx.prefix))
        return
    else:  # if not
        # get permissions of caller in current channel
        permissions = ctx.channel.permissions_for(ctx.author)
        # set needed permissions (manage roles)
        needed_perms = discord.Permissions(manage_roles=True)
        if needed_perms <= permissions:  # check permissions
            # if check successed
            # if @ in prefix
            if "@" in prefix:
                # send error message
                await ctx.send("Vous ne pouvez pas définir un préfixe qui contient @!")
                return
            # get settings for current guild
            data = await makeAsyncRequest(
                "SELECT * FROM settings WHERE GuildId = %s", (ctx.guild.id,)
            )
            # if we have record for current guild
            if data.__len__() > 0:
                # update it
                await makeAsyncRequest(
                    "UPDATE settings SET Prefix=%s WHERE GuildId=%s",
                    (
                        prefix,
                        ctx.guild.id,
                    ),
                )
            # else
            else:
                # create one
                await makeAsyncRequest(
                    "INSERT INTO settings (GuildId,Prefix,Type) VALUES (%s,%s,0)",
                    (
                        ctx.guild.id,
                        prefix,
                    ),
                )
            # send done message
            await ctx.send(t.l["fait"])
        # if check failed
        else:
            # send error message
            await ctx.send("Vous devez avoir la permission de gérer les rôles pour changer mon préfixe !")
            return


# main help command
@bot.command(brief="Besoin d'aide avec le bot ? C'est la bonne commande !")
async def help(ctx):
    time = datetime(2000, 1, 1, 0, 0, 0, 0)  # get time object
    # set title and timestamp of embed
    message = discord.Embed(title="Liste des commandes", timestamp=time.utcnow())
    # get current prefix
    prefix = ctx.prefix
    # set footer for embed
    message.set_footer(
        text=f"Demandé par {ctx.author.name} • Bot {conf.version} • GPLv3 ",
        icon_url=ctx.author.avatar.url,
    )
    # define value for Server section
    serverValue = f"""**`{prefix}server info`- Affiche les informations sur le serveur ajouté
`{prefix}server add <IP>:<Query port>`- Ajoute un serveur (Steam uniquement, officiel ou non) à votre liste
`{prefix}server delete`- Supprime le serveur de votre liste
`{prefix}server alias`- Liste des alias pour vos serveurs
`{prefix}server alias "<Alias>"`- Ajoute un alias pour un serveur
`{prefix}server alias delete`- Supprime l'alias de votre serveur**"""
    # add server section to the embed
    message.add_field(name=f"**Commandes du serveur:**", value=serverValue)
    # define value for notifications section
    notificationsValue = f"""**`{prefix}watch`- Le bot enverra un message lorsque le serveur sélectionné sera en ligne ou hors ligne dans le salon actuel.
`{prefix}unwatch` - Arrêtez de surveiller le serveur
`{prefix}automessage #tout_salon` - Le bot enverra un message de mise à jour sur un serveur !
`{prefix}automessage` - Liste des messages automatiques que vous avez
`{prefix}automessage delete` - Supprimer **tous** les messages automatiques d'un serveur
**"""
    # add notifications section to the embed
    message.add_field(
        name=f"**Commandes de notification:**", value=notificationsValue, inline=False
    )
    # define misc sections value
    miscValue = f"**`{prefix}info`- Obtenez des informations sur ce bot (par exemple, le serveur de support, GitHub, etc.)**"
    # add misc section to the embed
    message.add_field(name=f'**Commandes diverses :**', value=miscValue,
                      inline=False)
    # and send it  
    await ctx.send(embed=message)  


# ~~~~~~~~~~~~~~~~~~~~~
#        EVENTS
# ~~~~~~~~~~~~~~~~~~~~~

# will respond for ping of the bot
@bot.event
async def on_message(msg):  # on every message
    # if we in DMs  AND it isn't our message
    if msg.guild == None and msg.author != bot.user:
        try:
            # send error message

            await msg.channel.send(
                "Désolé, vous ne pouvez pas utiliser ce bot dans les DM!"
            )
        except BaseException as e:  # catch error
            return
        return  # ignore it we have no way to notify the user anyway
    # if content starts with ping with id of our bot
    # (first case is desktop ping and second is mobile ping)
    if msg.content.startswith(f"<@!{bot.user.id}>") or msg.content.startswith(f"<@{bot.user.id}>"):
        try:
            # send message and return
            await msg.channel.send(
                t.l["curr_prefix"].format(await get_prefix(bot, msg))
            )
            return
        except discord.errors.Forbidden:  # it was spaming me in DM's lol
            return
    await bot.process_commands(msg)  # if not process commands


# on error in some event
@bot.event
async def on_error(event, *args, **kwargs):
    # get tuple with exception and traceback https://docs.python.org/3/library/sys.html#sys.exc_info
    exception_pack = sys.exc_info()
    errors = traceback.format_exception(
        exception_pack[0], exception_pack[1], exception_pack[2]
    )
    errors_str = "".join(errors)
    msg = f"Une erreur s'est produite dans `{event}` event\n```{errors_str}```"
    if msg.__len__() >= 2000:
        await sendToMe(errors_str[:1975] + "`\nFin de la première partie", bot)
        await sendToMe(errors_str[1975:-1], bot, True)
        return
    else:
        await sendToMe(msg, bot, True)
        return


async def sendErrorEmbed(ctx, Id, error):
    # object to get time
    time = datetime(2000, 1, 1, 0, 0, 0, 0)
    # get config of bot
    cfg = config.Config()
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # set title
    embed.title = "Oups! Une erreur s'est produite !"
    # add info
    embed.add_field(
        name="J'en ai informé mon créateur ! Un correctif est déjà en route !",
        value=f"Votre id d'erreur **unique** est `{Id}`. Vous pouvez obtenir plus de soutien dans notre serveur [support](https://ocleiria.fr/discord).",
    )
    # add bot's version
    embed.set_footer(text=f"Bot {cfg.version}")
    # set embed's timestamp
    embed.timestamp = time.utcnow()
    try:
        # send embed
        await ctx.send(embed=embed)
    except:
        return


async def sendCommandNotFoundEmbed(ctx):
    # get prefix for this guild
    prefix = ctx.prefix
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add info
    embed.add_field(
        name="Tu as entré un mauvaise commande!",
        value=f"Commande `{ctx.message.content}` n'éxiste pas. Tu peux voir la liste des commande avec `{prefix}help`.",
    )
    # send embed
    await ctx.send(embed=embed)


async def rateLimitHit(ctx, error):
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = "Attendez!"
    # add info
    embed.add_field(
        name=f"Vous pouvez uniquement utiliser `{ctx.message.content}` uniquement `{error.cooldown.rate}` temp(s) par `{int(error.cooldown.per)}` seconde(s)!",
        value="Merci de retenter plutard.",
    )
    # send embed
    await ctx.send(embed=embed)


async def insufficientPerms(ctx, perms):
    # add \n to each permission
    joined = "\n".join(perms)
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'Il me manque certaines autorisations dans ce salon!'
    # add info
    embed.add_field(name="j'ai besoin:", value=f"```{joined}```")
    # send embed
    await ctx.send(embed=embed)


async def channelNotFound(ctx, error):
    # create embed
    embed = discord.Embed()
    # paint it red
    embed.color = discord.Colour.red()
    # add title
    embed.title = 'Ce salon n''a pas pu être trouvé !'
    # add info
    embed.add_field(name=f"Salon avec l'ID `{error.argument[2:-1]}` isn't found!",
                    value="Peut-être avez-vous copié ce canal depuis un autre serveur ? ")
    # send embed 
    await ctx.send(embed=embed)


@bot.check
async def check_commands(ctx):
    # 1661904000 - 31'th of August 2022 in unix timestamp
    # https://support-dev.discord.com/hc/en-us/articles/4404772028055-Message-Content-Privileged-Intent-for-Verified-Bots
    if getattr(conf, "deprecation", True) and not is_slash(ctx):
        messages_left = bot.deprecation_warnings.get(ctx.guild.id,3)
        if messages_left < 0:
            return True
        embed = discord.Embed()
        embed.title = "Notice!"
        embed.colour = discord.Colour.red()
        embed.add_field(
            name="Les commandes régulières vont **cesser** de fonctionner sur <t:1661904000:D> (<t:1661904000:R>)!",
            value="Au lieu de cela, il y aura de nouvelles commandes slash.",
        )
        embed.add_field(
            name=f"Pour vérifier si vous êtes prêt pour le changement, utilisez la commande `{ctx.prefix}validateSlash`.",
            value="Aucune donnée ne sera perdue après la transition!",
        )
        embed.set_footer(text=f"Vous obtiendrez {messages_left} de nouveaux avertissements aujourd'hui.")
        try:
            await ctx.send(embed=embed)
        except:
            return True
        bot.deprecation_warnings[ctx.guild.id] = messages_left - 1
    return True


@bot.event
async def on_command_error(ctx, error):
    # get original error from d.py error
    # if none it will be set to error itself
    origError = getattr(error, "original", error)
    # get type of an error
    errorType = type(error)
    # long if elif statement
    # if some command isn't found
    if errorType == discord.ext.commands.errors.CommandNotFound:
        try:
            # try to send an error embed
            await sendCommandNotFoundEmbed(ctx)
            return
        # if we can't
        except discord.errors.Forbidden:
            # return
            return
    # if some channel isn't found
    if errorType == discord.ext.commands.errors.ChannelNotFound:
        await channelNotFound(ctx, error)
        return
    # if some check failed
    elif errorType == discord.ext.commands.errors.CheckFailure:
        # do nothing
        # (it doesn't have any info on what has failed)
        return
    # if someone hit ratelimit
    elif errorType == discord.ext.commands.CommandOnCooldown:
        # send an embed about it
        await rateLimitHit(ctx, error)
        return
    # if bot need some permissions
    elif errorType == discord.ext.commands.BotMissingPermissions:
        try:
            # try to get what we are missing
            missing = error.missing_permissions
        # if we can't
        except AttributeError:
            # get it from original error
            missing = origError.missing_permissions
        # n is how a permission is called in API
        # n + 1 is it's replacement for message
        map = [
            "manage_messages",
            "Gérer les messages",
            "external_emojis",
            "Use external emojis",
            "add_reactions",
            "Utiliser des emojis externes",
        ]
        # array with replaced permissions names
        needed = []
        # for each permission
        for perm in missing:
            # if permission is in list
            if perm in map:
                # put it's replacement
                needed.append(map[map.index(perm) + 1])
            # if not
            else:
                # put it as is
                needed.append(perm)
        # send embed about it
        await insufficientPerms(ctx, needed)
        return
    # if bot is missing some permissions
    elif errorType == discord.errors.Forbidden:
        # add some of them to the list
        needed_perms = [
            "Ajouter des réactions",
            "Use external emojis",
            "Envoyer et voir les messages",
            "Gérer les messages",
        ]
        try:
            # try to send message
            await insufficientPerms(ctx, needed_perms)
            return
        # if we can't
        except discord.Forbidden:
            # return
            return
    # if required parameter is missing
    elif errorType == discord.ext.commands.errors.MissingRequiredArgument:
        embed = discord.Embed(
            title="Le paramètre requis est manquant !", color=discord.Color.red()
        )
        embed.add_field(
            name=f"Paramètre `{error.param.name}` est requis !", value="\u200B"
        )
        await ctx.send(embed=embed)
        return
    # debug
    # I really need some good logging system
    debug.debug("Entered error handler")
    # format exception
    errors = traceback.format_exception(type(error), error, error.__traceback__)
    # get current time
    Time = int(time.time())
    # insert error record into DB
    await makeAsyncRequest(
        "INSERT INTO errors(Error, Time, UserDiscordId, ChannelDiscordId, GuildDiscordId, Message) VALUES (%s,%s,%s,%s,%s,%s)",
        (
            json.dumps(errors),
            Time,
            ctx.author.id,
            ctx.channel.id,
            ctx.guild.id,
            ctx.message.content,
        ),
    )
    # select inserted error record
    data = await makeAsyncRequest("SELECT * FROM errors WHERE Time=%s", (Time,))
    # get it's id
    Id = data[0][0]
    # send error embed with this id
    await sendErrorEmbed(ctx, Id, error)
    # add each error together
    errors_str = "".join(errors)
    # format time
    date = datetime.utcfromtimestamp(Time).strftime("%Y-%m-%d %H:%M:%S")
    # format message for me
    message = f"""
Error happened! 
`{errors_str}`
Error id : `{Id}`
Message : `{ctx.message.content}`
Error happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
    """
    # if message has over 2k characters
    if message.__len__() >= 2000:
        try:
            # send it in chunks
            await sendToMe(message[:1975] + "`\nEnd of first part", bot)
            await sendToMe(message[1975:-1], bot, True)
        # if we can't
        except BaseException as e:
            await sendToMe("La longueur du message d'erreur est supérieure à 4k !", bot, True)
            await sendToMe(
                f"""Error id : `{Id}`
Message : `{ctx.message.content}`
When this happened : `{date}`
Guild name : `{ctx.guild.name}`
Guild id : `{ctx.guild.id}`
Error : {e}""",
                bot,
            )
    else:
        await sendToMe(message, bot, True)


setup()
# was causing problems and was using python implementation of asyncio instead of C one (which is faster)
# nest_asyncio.apply() # patch loop https://pypi.org/project/nest-asyncio/
bot.run(conf.token)  # get our discord token and FIRE IT UP !
