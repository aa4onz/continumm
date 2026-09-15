import time
import re
import asyncio  
from variables import *
from utils import deadline, score_up, race_up, get_main
import task, role, composter, menus  
from discord.ext import commands 
from discord import app_commands  
from apscheduler.triggers.interval import IntervalTrigger

async def ready():
    print("Bot ready.")
    deadline()
    for row in list(db_alt.find()): 
        alts[str(row["_id"])] = str(row["main_id"])
        
    # Register the persistent SaveLockView components right here on boot!
    bot.add_view(menus.SaveLockView())
    
    cron.add_job(task.check_winners, IntervalTrigger(hours=1))
    cron.start()
    await bot.tree.sync()

async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("only for server administrators.", delete_after=5)
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
    if msg.embeds:
        for embed in msg.embeds:
            if embed.title and "Community Composter" in embed.title:
                result_embed = composter.parse_and_optimize(embed)
                await msg.reply(embed=result_embed)
                return 
    cid = str(msg.channel.id)

    # ⚠️ INTERCEPT AUTOMATED GUILD SAVES IMMEDIATELY AT THE TOP
    if msg.author.id == b1 and "You have used **1** guild save!" in msg.content:
        await msg.channel.set_permissions(msg.guild.default_role, send_messages=False)
        
        current_tiers = t if cid == c1 else ct
        for tier_name in current_tiers:
            role_obj = d.utils.get(msg.guild.roles, name=tier_name)
            if role_obj:
                await msg.channel.set_permissions(role_obj, send_messages=False)
                
        alt_role = d.utils.get(msg.guild.roles, name="alt")
        if alt_role:
            await msg.channel.set_permissions(alt_role, send_messages=False)
            
        for bot_id in [b1, b2, 989473317683617872]:
            bot_member = msg.guild.get_member(bot_id)
            if bot_member:
                await msg.channel.set_permissions(bot_member, view_channel=True, send_messages=True, add_reactions=True)
                
        btn_view = menus.SaveLockView()
        btn_msg = await msg.channel.send(view=btn_view)
        
        async def auto_timeout_lock(target_msg, view_instance):
            await asyncio.sleep(5)
            try:
                current_msg = await msg.channel.fetch_message(target_msg.id)
                if current_msg and len(current_msg.components) > 0:
                    btn = view_instance.children[0]
                    if not btn.disabled:
                        btn.disabled = True
                        btn.style = d.ButtonStyle.secondary
                        await current_msg.edit(view=view_instance)
                        await msg.channel.send("channel locked")
            except:
                pass

        bot.loop.create_task(auto_timeout_lock(btn_msg, btn_view))
        return

    if cid == c3 and msg.embeds and msg.author.id in [b1, b2]:
        return await role.check_and_update(msg, msg.author.id)
        
    if msg.author.bot: 
        return

    ctx = await bot.get_context(msg)
    if ctx.valid:
        return

    if cid not in ch: 
        return

    # SMART MIXED TEXT PARSING VIA REGEX
    body = msg.content.strip()
    match = re.match(r"^(\d+)", body)
    if not match: 
        return
        
    num = int(match.group(1))
    active_user = get_main(msg.author.id)

    st = cache[cid]
    if st["n"] is None: 
        st["n"], st["u"] = num - 1, None
    if num != st["n"] + 1 or active_user == st["u"]: 
        st["n"], st["u"] = num, active_user
        return

    st["n"], st["u"] = num, active_user
    score_up(msg.author.id)

    # ACCURATE RACE METRIC TRACKING
    rc = db_rc.find_one({"_id": f"race_{cid}"})
    if rc:
        current_time = time.time()
        uid_str = str(msg.author.id)
        
        update_payload = {
            "$set": {
                "last_num": num,
                "last_time": current_time,
                f"players.{uid_str}": True
            }
        }
        
        if rc.get("start_num") is None:
            update_payload["$set"]["start_num"] = num
            update_payload["$set"]["start_time"] = current_time

        db_rc.update_one({"_id": f"race_{cid}"}, update_payload)

def register():
    bot.add_listener(ready, 'on_ready')
    bot.add_listener(message, 'on_message')
    bot.add_listener(command_error, 'on_command_error')
    bot.tree.error(app_error)
