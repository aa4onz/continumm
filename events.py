import time
from variables import *
from utils import deadline, score_up, race_up, get_main
import task, role
from discord.ext import commands 
from discord import app_commands  
from apscheduler.triggers.interval import IntervalTrigger

async def ready():
    print("Bot ready.")
    deadline()
    for row in list(db_alt.find()): 
        alts[str(row["_id"])] = str(row["main_id"])
    cron.add_job(task.check_winners, IntervalTrigger(hours=1))
    cron.start()
    await bot.tree.sync()

async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("only server administrators can use this command.", delete_after=5)
        return
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"[ERROR] Prefix exception: {error}")

async def app_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "Only server administrators can use this command."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return
    print(f"[ERROR] Slash exception: {error}")

async def message(msg):
    cid = str(msg.channel.id)

    if cid == c3 and msg.embeds and msg.author.id in [b1, b2]:
        return await role.check_and_update(msg, msg.author.id)
    if msg.author.bot: 
        return

    ctx = await bot.get_context(msg)
    if ctx.valid:
        return

    if cid not in ch: 
        return

    if "You have used **1** guild save!" in msg.content and msg.author.id == b1:
        return await msg.channel.set_permissions(msg.guild.default_role, send_messages=False)

    body = msg.content.strip()
    if not body.isdigit() or str(int(body)) != body: 
        return
    num = int(body)

    active_user = get_main(msg.author.id)

    st = cache[cid]
    if st["n"] is None: 
        st["n"], st["u"] = num - 1, None
    if num != st["n"] + 1 or active_user == st["u"]: 
        st["n"], st["u"] = num, active_user
        return

    st["n"], st["u"] = num, active_user
    score_up(msg.author.id)

    rc = db_rc.find_one({"_id": f"race_{cid}"})
    if rc:
        if rc.get("start_time") is None: 
            db_rc.update_one({"_id": f"race_{cid}"}, {"$set": {"start_time": time.time()}})
        race_up(cid, msg.author.id)

def register():
    bot.add_listener(ready, 'on_ready')
    bot.add_listener(message, 'on_message')
    bot.add_listener(command_error, 'on_command_error')
    bot.tree.error(app_error)
