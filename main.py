import asyncio, json, roblox, firebase_admin, requests, os, interactions
from asgiref.wsgi import WsgiToAsgi
from dotenv import load_dotenv
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
from hypercorn.asyncio import serve
from hypercorn.config import Config
from interactions.ext import molter

from classes.robloxHandler import RobloxStuff
robloxLib = RobloxStuff()

from classes.verification import verification
verifHandler = verification()

from roblox import Client 

client = Client(os.environ["ROBLOX_COOKIE"])


app = Flask(__name__)
config = Config()
config.bind = ["0.0.0.0:5000"] #0.0.0.0:5000

load_dotenv()

bot = interactions.Client(
token=os.environ["TOKEN"], 
intents= interactions.Intents.ALL | interactions.Intents.GUILD_MESSAGE_CONTENT)

cred = credentials.Certificate("configurations/project-scpf-firebase-adminsdk-q8rkn-aec3853ae6.json")

default_app = firebase_admin.initialize_app(cred, {
	    'databaseURL': "https://project-scpf-default-rtdb.firebaseio.com"
})


molter.setup(bot, default_prefix="?")

# commands folder
bot.load("slashCommands.economy")
bot.load("slashCommands.information")
bot.load("slashCommands.roles")
bot.load("slashCommands.verification")

# misc folder 
bot.load("misc.appDirectory")
bot.load("prefixedCommands.prefix")
# bot.load("misc.verifrewrite")

# events folder 
bot.load("events.autoModeration")
bot.load("events.contribute")
bot.load("events.misc")
bot.load("events.moderation")
bot.load("events.joins")

# tasks folder 
bot.load("tasks.changepresense")
bot.load("tasks.qotd")
bot.load("tasks.holidays")

@app.route('/')
async def homePage():
    return "Nothing for you here."


# @app.route("/changedevproduct", methods=["POST", "GET"])
# async def changeDevProduct():
#     if request.headers["DEVPRODUCT_API_KEY"] == os.environ["DEVPRODUCT_API_KEY"]:
#         developerProductId = 1330724291
#         universeId = 3071466236
        
#         priceInRobux = request.get_json()["priceInRobux"]
#         devLink = f"https://develop.roblox.com/v1/universes/{universeId}/developerproducts/{developerProductId}/update"

#         something = await client.requests.post(devLink, json={
#             "PriceInRobux": priceInRobux,
#         })
#         print(something.status_code)
#         return "Hello, world!"

@app.route('/applications', methods=['GET', 'POST'])
async def applicationPage():
    if request.headers["API-KEY"] == os.environ["APPLICATION_API_KEY"]:
        data = request.json 

        embed1 = interactions.Embed()
        for value in data:
            try:
                embed1.add_field(name=value["Question"], value=value["Response"], inline=False)
            except KeyError:
                pass

    
        button = interactions.Button(style=interactions.ButtonStyle.PRIMARY, label="Accept", custom_id="accept")
        button2 = interactions.Button(style=interactions.ButtonStyle.DANGER, label="Decline", custom_id="decline")

        @bot.component("accept")
        async def button_response(ctx): 
            modal = interactions.Modal(
                title="Accept Form",
                custom_id="accept_form",
                components=[
                    interactions.TextInput(
                        style=interactions.TextStyleType.SHORT,
                        label="Reason",
                        custom_id="text_input_response",
                        min_length=1,
                        max_length=100,
                    )

                ],
            )

            await ctx.popup(modal)
            await ctx.send("Follow the prompt on your screen.", ephemeral=True)

        @bot.component("decline")
        async def button_response2(ctx):
            modal = interactions.Modal(
                title="Decline Form",
                custom_id="decline_form",
                components=[
                    interactions.TextInput(
                        style=interactions.TextStyleType.SHORT,
                        label="Reason",
                        custom_id="text_input_response",
                        min_length=1,
                        max_length=100,
                    )

                ],
            )
            await ctx.popup(modal)
            await ctx.send("Follow the prompt on your screen.", ephemeral=True)
            

        e = await interactions.get(bot, interactions.Channel, object_id=1014158879363432520)

        robloxId = data[-1]["robloxId"]
        applicationType = data[-1]["ApplTitle"]
        robloxName = data[-1]["robloxName"]

        robloxInfoTBL = await robloxLib.get_roblox_info_from_roblox(robloxId)

        discordUser = robloxInfoTBL["user"]["id"] or robloxName 
                
        discordUserToId = robloxInfoTBL["user"]["id"]
        msg = await e.send(f"{robloxName}",  embeds=embed1, components=[button, button2])

        channel2 = await interactions.get(bot, interactions.Channel, object_id=997213401799462973)

        member = await interactions.get(bot, interactions.Member, object_id=discordUserToId, parent_id=864557936068395018)

        user = await client.get_user(robloxId)
        user_thumbnails = await client.thumbnails.get_user_avatar_thumbnails(
            users=[user],
            type=roblox.AvatarThumbnailType.headshot,
            size=(420, 420)
        ) 

        if len(user_thumbnails) > 0:
            user_thumbnail = user_thumbnails[0]
        
        @bot.modal("accept_form")
        async def modal_response(ctx: interactions.CommandContext, response: str):
            rankType = None 
            
            if applicationType == "Security Clearance 0" and rankType == None and robloxName.lower() != "bulldo344":
                await robloxLib.set_rank(robloxName, 3)
            elif applicationType == "Security Clearance 1" and rankType == None and robloxName.lower() != "bulldo344":
                await robloxLib.set_rank(robloxName, 225)
            
            embed1 = interactions.Embed(name=robloxId, description=f"{robloxName}'s {applicationType} has been accepted. You have been automatically updated.")
            embed1.add_field(name="Reason", value=response, inline=False)
            
            embed1.set_thumbnail(user_thumbnail.image_url)
            
            await channel2.send(member.mention, embeds=embed1)
            
            await verifHandler.updateInDepartmentGroup(bot, member.id)
            await verifHandler.updateInMainGroup(bot, member.id)       
            await verifHandler.changeNickname(bot, member)  

            await ctx.send("Sent Response", ephemeral=True)
            return 

        @bot.modal("decline_form")
        async def modal_response(ctx: interactions.CommandContext, response: str):
            embed1 = interactions.Embed(name=robloxId, description=f"{robloxName}'s {applicationType} has been declined. They have not been updated.")
            embed1.add_field(name="Reason", value=response, inline=False)
            
            embed1.set_thumbnail(user_thumbnail.image_url)
            
            await channel2.send(member.mention, embeds=embed1)
            
            await msg.delete()
            await ctx.send("Sent Response", ephemeral=True)
            return 

        return "hello, world!"


loop = asyncio.get_event_loop()

task1 = loop.create_task((serve(WsgiToAsgi(app), config)))
task2 = loop.create_task(bot._ready())

gathered = asyncio.gather(task1, task2)
loop.run_until_complete(gathered)
