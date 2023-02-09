from cogs.utils.helpers import *
import discord
import cogs.utils.menus as m
import datetime


class AutoMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def done(self, ctx, serverRecord, msgId, channel):
        # make link to that message
        link = f"https://discordapp.com/channels/{ctx.guild.id}/{channel.id}/{msgId}"
        # construct server object
        server = c.ARKServer.fromJSON(serverRecord[4])
        # construct embed
        embed = discord.Embed()
        # add info
        embed.add_field(
            name=f"C'est fait !",
            value=f"Je vais mettre à jour ce [message]({link}) sur `{await stripVersion(server)}`!",
        )
        # paint it
        embed.color = randomColor()
        # and send it
        await ctx.send(embed=embed)

    async def noRecordsForServer(self, ctx, serverRecord):
        # construct server object
        server = c.ARKServer.fromJSON(serverRecord[4])
        # construct embed
        embed = discord.Embed()
        # add info
        embed.add_field(
            name=f"Vous n'avez pas de messages automatiques pour `{await stripVersion(server)}`!",
            value=f"Vous pouvez les créer avec `{ctx.prefix}automessage #Salon-que-tu-veux :`",
        )
        # paint it
        embed.color = randomColor()
        # and send it
        await ctx.send(embed=embed)

    async def alreadyHave(self, ctx, serverRecord, autoMessageRecord):
        # make link to that message
        link = f"https://discordapp.com/channels/{ctx.guild.id}/{autoMessageRecord[1]}/{autoMessageRecord[2]}"
        # construct server object
        server = c.ARKServer.fromJSON(serverRecord[4])
        # construct embed
        embed = discord.Embed()
        # add info
        embed.add_field(
            name=f"Vous avez déjà un message automatique pour `{await stripVersion(server)}` sur ce salon !",
            value=f"Vous avez déjà l'auto [message]({link}) pour `{await stripVersion(server)}` sur ce salon !",
        )
        # paint it
        embed.color = randomColor()
        # and send it
        await ctx.send(embed=embed)

    async def listMessages(self, ctx, messages):
        # if no messages to list
        if messages.__len__() <= 0:
            # create error embed
            errorEmbed = discord.Embed()
            # add error info
            errorEmbed.add_field(
                name="Oups, il semble que vous n'ayez pas de messages automatiques !",
                value=f"Mais vous pouvez les ajouter via {ctx.prefix}automessage #Salon-que-tu-veux",
            )
            # paint it
            errorEmbed.color = randomColor()
            # send embed
            await ctx.send(embed=errorEmbed)
            return

        # create embed
        embed = discord.Embed(title="Liste des messages automatiques :")
        # index of a message
        i = 1
        # for each message
        for message in messages:
            # get alias (if any) for current server
            alias = await getAlias(message[3], ctx.guild.id)
            # select server object for current server
            server = await makeAsyncRequest(
                "SELECT ServerObj FROM servers WHERE Id=%s", (message[3],)
            )
            # create server object from record
            serverObj = c.ARKServer.fromJSON(server[0][0])
            # if we have alias put it in name
            # else put server's name there
            name = await stripVersion(serverObj) if alias == "" else alias
            # construct message link from ids
            link = f"https://discordapp.com/channels/{ctx.guild.id}/{message[1]}/{message[2]}"
            # create channel mention
            channelMention = f"<#{message[1]}>"
            # add info about current message
            embed.add_field(
                name=f"{i}) Message pour {name}:",
                value=f"[Message]({link}) dans {channelMention}",
            )
            # increase message index
            i += 1
        # send list
        await ctx.send(embed=embed)

    async def deleteAutoMessage(self, ctx):
        # construct selector menu
        selector = m.Selector(ctx, self.bot, c.Translation())
        # present selector
        serverIp = await selector.select()
        # if nothing was selected
        if serverIp == "":
            # return
            return
        # else select servers with such ip
        server = await makeAsyncRequest(
            "SELECT * FROM servers WHERE Ip=%s", (serverIp.ip,)
        )
        # and select first one
        server = server[0]
        # select all automessage records for this discord and ARK server
        messages = await makeAsyncRequest(
            "SELECT * FROM automessages WHERE ServerId=%s AND DiscordGuildId=%s",
            (
                server[0],
                ctx.guild.id,
            ),
        )
        # if we have no records
        if messages.__len__() <= 0:
            # send embed
            await self.noRecordsForServer(ctx, server)
            return
        # if we have some records
        else:
            # create server object from server record
            serverObj = c.ARKServer.fromJSON(server[4])
            # get alias (if any)
            alias = await getAlias(server[0], ctx.guild.id)
            # set name to alias if we have one
            # else set it to name of the server
            name = await stripVersion(serverObj) if alias == "" else alias
            # create embed
            embed = discord.Embed(title=f"Supprimer tous les messages pour `{name}`?")
            i = 1
            # for each message
            for message in messages:
                # make link to discord message
                link = f"https://discordapp.com/channels/{ctx.guild.id}/{message[1]}/{message[2]}"
                # make channel mention
                channelMention = f"<#{message[1]}>"
                # add info about message
                embed.add_field(
                    name=f"Message №{i}",
                    value=f"[Message]({link}) dans {channelMention}",
                )
                # increase i
                i += 1
            # send embed
            msg = await ctx.send(embed=embed)
            # workaround
            # might mess up
            self.msg = msg
            # add two reactions
            await msg.add_reaction("✅")
            await msg.add_reaction("❎")
            try:
                # wait for user to react
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    timeout=100,
                    check=lambda r, user: user != self.bot.user
                    and r.message.id == self.msg.id,
                )
            # if waited too long
            except asyncio.TimeoutError:
                try:
                    # clear reactions
                    await self.msg.clear_reactions()
                    # Reset embed
                    await self.msg.edit(
                        content="Le menu interactif était fermé.", embed=None
                    )
                except discord.errors.NotFound:  # the menu was deleted
                    return
            # if user had reacted
            else:
                # if user wants to delete auto message record
                if str(reaction.emoji) == "✅":
                    # clear reactions
                    await self.msg.clear_reactions()
                    # delete record
                    await makeAsyncRequest(
                        "DELETE FROM automessages WHERE ServerId=%s", (server[0],)
                    )
                    # notify user
                    await self.msg.edit(
                        content="C'est fait ! Vous pouvez maintenant supprimer ce message en toute sécurité !",
                        embed=None,
                    )
                    return
                # if user doesn't want to delete auto message
                if str(reaction.emoji) == "❎":
                    # delete message
                    await self.msg.delete()
                    return

    async def makeMessage(self, serverId, guildId, serverIp=""):
        # if we have server ip
        if serverIp != "":
            # select a server by it
            server = await makeAsyncRequest(
                "SELECT * FROM servers WHERE Ip=%s", (serverIp,)
            )
        # else we gave it's id
        else:
            # select a server by id
            server = await makeAsyncRequest(
                "SELECT * FROM servers WHERE Id=%s", (serverId,)
            )
        # create server and players on it from server record
        serverObj = c.ARKServer.fromJSON(server[0][4])
        playersObj = c.PlayersList.fromJSON(server[0][5])
        # get server's alias
        alias = await getAlias(serverId, guildId)
        # if we have alias
        if alias != "":
            # use it
            name = alias
        # else
        else:
            # use server's name
            name = await stripVersion(serverObj)
        # create embed
        embed = discord.Embed(title=name)
        # if there are any players
        if playersObj.list.__len__() > 0:
            # variables
            nameValue = ""
            timevalue = ""
            # for each player in list
            for player in playersObj.list:
                # and it's name and time to variables
                nameValue += f"{player.name}\n"
                timevalue += f"{player.time}\n"
            # then add these variables to embed
            embed.add_field(name="Nom", value=nameValue, inline=True)
            embed.add_field(name="Temps", value=timevalue, inline=True)
        # if there is no players
        else:
            # add this info into embed
            embed.add_field(name="Personne n'est sur le serveur", value="\u200B", inline=True)
        # if server is online set status to online string
        # else set to offline string
        status = (
            ":green_circle: En Ligne" if server[0][6] == 1 else ":red_circle: Hors Ligne"
        )
        # add other info about server
        embed.add_field(name="Statut", value=status, inline=False)
        embed.add_field(name="Ping", value=f"{serverObj.ping} ms", inline=True)
        embed.add_field(name="Map", value=serverObj.map, inline=True)
        embed.add_field(name="IP", value=f"{serverObj.ip}", inline=True)
        # get current time
        curTime = datetime.datetime.utcnow()
        # set footer
        embed.set_footer(text=f'Mis à jour : {curTime.strftime("%m.%d à %H:%M")} (UTC)')
        # paint in random color
        embed.color = randomColor()
        # return embed
        return embed

    async def noPerms(self, ctx, channel, perms):
        # list with needed perms
        boolPerms = [perms.send_messages, perms.embed_links, perms.external_emojis]
        # list with text representations of perms in first list
        textPerms = ["Envoyer des messages", "Intégrer des liens", "Utiliser des émojis externes"]
        # where we put text representations of needed perms
        neededPerms = []
        for i, perm in enumerate(boolPerms):
            # if perm is false
            if not perm:
                # append to needed perms
                # text representation from
                # textPerms
                neededPerms.append(textPerms[i])
                pass
        # join each needed perm
        neededPerms = " , ".join(neededPerms)
        # create embed
        embed = discord.Embed()
        # set color
        embed.color = discord.Colour.red()
        # add info
        embed.add_field(
            name="Je n'ai pas assez de permissions dans ce canal !",
            value=f"J'ai besoin `{neededPerms}` dans {channel.mention} pour y envoyer des messages automatiques !",
        )
        # send embed
        await ctx.send(embed=embed)

    async def checkPermissions(self, channel, ctx):
        # return True
        # get our bot member in current guild
        botMember = ctx.guild.me
        # get permissions
        perms = channel.permissions_for(botMember)
        # if bot have permissions:
        # send messages
        # embed links
        # use external emojis
        if perms.send_messages and perms.embed_links and perms.external_emojis:
            # return true
            return True
        else:
            # send error embed
            await self.noPerms(ctx, channel, perms)
            # return false
            return False

    @commands.group(
        invoke_without_command=True,
        case_insensitive=True,
        brief="Commande de base pour les messages automatiques du bot",
    )
    async def automessage(self, ctx):
        embed = discord.Embed(title="Aucune sous-commande sélectionnée !")
        embed.add_field(name="Sous-commandes possibles :", value="```\nadd\ndelete\nlist```")
        embed.add_field(
            name="Exemple de sous-commande `add` :", value=f"`{ctx.prefix}automessage add`"
        )
        await ctx.send(embed=embed)

    @automessage.command(brief="Une commande pour créer un automessage")
    async def add(
        self,
        ctx,
        channel: discord.TextChannel = commands.Option(
            description="Salon où envoyer les messages automatiques"
        ),
    ):
        # check perms
        if not await self.checkPermissions(channel, ctx):
            # if failed return
            # function handled error message
            return
        # create selector
        selector = m.Selector(ctx, self.bot, c.Translation())
        # present selector
        server_obj = await selector.select()
        # if nothing was selected
        if server_obj == "":
            # return
            return
        # select server record by ip returned by selector
        server = await makeAsyncRequest(
            "SELECT * FROM servers WHERE Ip=%s", (server_obj.ip,)
        )
        # select all automessage records for current ARK server
        automessages = await makeAsyncRequest(
            "SELECT * FROM automessages WHERE ServerId = %s", (server[0][0])
        )
        # if we have some records
        if automessages.__len__() >= 1:
            # for each record
            for automessage in automessages:
                # check if it is for current channel
                if automessage[1] == channel.id:
                    # if so then notify user about it
                    await self.alreadyHave(ctx, server[0], automessages[0])
                    # and return
                    return
        # else
        try:
            # try to send message
            message = await channel.send(
                embed=await self.makeMessage(0, channel.guild.id, server_obj.ip)
            )
        # if we can't
        except discord.Forbidden:
            # notify user
            await ctx.send("Impossible d'envoyer un message au canal sélectionné !")
            return
        # else
        # make new record
        await makeAsyncRequest(
            "INSERT INTO automessages (`DiscordChannelId`, `DiscordMsgId`, `ServerId`, `DiscordGuildId`) VALUES (%s,%s,%s,%s)",
            (
                channel.id,
                message.id,
                server[0][0],
                ctx.guild.id,
            ),
        )
        # and notify user
        await self.done(ctx, server[0], message.id, channel)

    @automessage.command(brief="Une commande listant tous les messages automatiques avec des liens vers eux")
    async def list(
        self,
        ctx,
    ):
        # select all auto messages for this server
        messages = await makeAsyncRequest(
            "SELECT * FROM automessages WHERE DiscordGuildId=%s", (ctx.guild.id,)
        )
        # and list them
        await self.listMessages(ctx, messages)

    @automessage.command(brief="Une commande pour supprimer un message automatique")
    async def delete(
        self,
        ctx,
    ):
        await self.deleteAutoMessage(ctx)

    # @commands.bot_has_permissions(
    #     add_reactions=True,
    #     read_messages=True,
    #     send_messages=True,
    #     manage_messages=True,
    #     external_emojis=True,
    # )
    # @commands.command()
    # async def old_automessage(self, ctx, *agrs):
    #     # construct converter
    #     channel_converter = discord.ext.commands.TextChannelConverter()
    #     try:
    #         # try to convert first arg
    #         channel = await channel_converter.convert(ctx, agrs[0])
    #     # if we can't
    #     except discord.ext.commands.BadArgument as e:
    #         # and we don't need to delete server
    #         if agrs[0] != "delete":
    #             # re-raise
    #             # error handle will handle this
    #             raise e
    #         # if we need to delete server
    #         else:
    #             await self.deleteAutoMessage(ctx)
    #             return
    #     # we need to list all servers
    #     except IndexError:
    #         # select all auto messages for this server
    #         messages = await makeAsyncRequest(
    #             "SELECT * FROM automessages WHERE DiscordGuildId=%s", (ctx.guild.id,)
    #         )
    #         # and list them
    #         await self.listMessages(ctx, messages)
    #         return
    #     # we need to add record in db
    #     # check perms
    #     if not await self.checkPermissions(channel, ctx):
    #         # if failed return
    #         # function handled error message
    #         return
    #     # create selector
    #     selector = m.Selector(ctx, self.bot, c.Translation())
    #     # present selector
    #     serverIp = await selector.select()
    #     # if nothing was selected
    #     if serverIp == "":
    #         # return
    #         return
    #     # select server record by ip returned by selector
    #     server = await makeAsyncRequest(
    #         "SELECT * FROM servers WHERE Ip=%s", (serverIp.ip,)
    #     )
    #     # select all automessage records for current ARK server
    #     automessages = await makeAsyncRequest(
    #         "SELECT * FROM automessages WHERE ServerId = %s", (server[0][0])
    #     )
    #     # if we have some record
    #     if automessages.__len__() >= 1:
    #         # and it is for the same channel
    #         if automessages[0][1] == channel.id:
    #             # notify user about it
    #             await self.alreadyHave(ctx, server[0], automessages[0])
    #             return
    #     # else
    #     try:
    #         # try to send message
    #         message = await channel.send(
    #             embed=await self.makeMessage(0, channel.guild.id, serverIp.ip)
    #         )
    #     # if we can't
    #     except discord.Forbidden:
    #         # notify user
    #         await ctx.send("Cannot send message to selected channel!")
    #         return
    #     # else
    #     # make new record
    #     await makeAsyncRequest(
    #         "INSERT INTO automessages (`DiscordChannelId`, `DiscordMsgId`, `ServerId`, `DiscordGuildId`) VALUES (%s,%s,%s,%s)",
    #         (
    #             channel.id,
    #             message.id,
    #             server[0][0],
    #             ctx.guild.id,
    #         ),
    #     )
    #     # and notify user
    #     await self.done(ctx, server[0], message.id, channel)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AutoMessageCog(bot))
