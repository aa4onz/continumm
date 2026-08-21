
# ==============================================================================
# PART 1: CLIENT INITIALIZATION & BOT INSTANTIATION
# ==============================================================================
import os
import re
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import certifi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class CountingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="r!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally successfully!")

bot = CountingBot()






# ==============================================================================
# PART 2: ENVIRONMENTAL VARIABLES & ROLE MILESTONE TIERS
# ==============================================================================
TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

COUNTING_BOT_ID = 510016054391734273        # Official Counting Bot ID
CLASSIC_BOT_ID = 639599059036012605          # Classic Counting Bot IDD

c1 = str(os.getenv('c1')).strip()            # Regular Counting Channel ID
c2 = str(os.getenv('c2')).strip()            # Classic Counting Channel ID
c3 = str(os.getenv('c3')).strip()            # Bot Command Channel ID (#c-command)

COUNTING_CHANNELS = [c1, c2]

# Lightning-fast local memory cache to eliminate database lag and internet latency
MEMORY_STREAKS = {
    c1: {"current_count": None, "last_user_id": None},
    c2: {"current_count": None, "last_user_id": None}
}

STANDARD_TIERS = [
    (3000000, 3999999, "3000000"), (2000000, 2999999, "2000000"),
    (1000000, 1999999, "1000000"), (750000,  999999,  "750000"),
    (500000,  749999,  "500000"),  (250000,  499999,  "250000"),
    (100000,  249999,  "100000"),  (75000,   99999,   "75000"),
    (50000,   74999,   "50000"),   (25000,   49999,   "25000"),
    (10000,   24999,   "10000"),   (5000,    9999,    "5000")
]

CLASSIC_TIERS = [(min_v, max_v, f"{name}c") for min_v, max_v, name in STANDARD_TIERS]

ALL_STANDARD_NAMES = [t[2] for t in STANDARD_TIERS]
ALL_CLASSIC_NAMES = [t[2] for t in CLASSIC_TIERS]


# ==============================================================================
# PART 3: CLOUD STORAGE DATABASE CONNECTIONS
# ==============================================================================
try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client["counting_bot_db"]
    leaderboard_collection = db["leaderboard"]
    system_collection = db["system_state"]
    races_collection = db["active_races"]
    top_races_collection = db["top_races"]
    print("Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

scheduler = AsyncIOScheduler()

# ==============================================================================
# PART 4: BACKGROUND JOBS & SCORING MATRICES
# ==============================================================================
def get_tournament_deadline():
    timer = system_collection.find_one({"_id": "global_tournament"})
    if not timer:
        deadline = datetime.now(timezone.utc) + timedelta(days=14)
        new_timer = {"_id": "global_tournament", "end_date": deadline}
        system_collection.insert_one(new_timer)
        return new_timer
    return timer

def increment_global_score(user_id):
    leaderboard_collection.update_one(
        {"_id": str(user_id)},  
        {"$inc": {"correct_counts": 1}},
        upsert=True
    )

def log_race_contribution(channel_id, user_id):
    races_collection.update_one(
        {"_id": f"race_{channel_id}"},
        {"$inc": {f"players.{user_id}": 1, "total_counts": 1}}
    )

async def check_and_announce_winners():
    timer = get_tournament_deadline()
    deadline = timer.get("end_date")
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) < deadline:
        return

    top_user = leaderboard_collection.find_one(sort=[("correct_counts", -1)])

    for ch_id_str in COUNTING_CHANNELS:
        try:
            channel = bot.get_channel(int(ch_id_str))
            if not channel: continue
            if top_user and top_user.get("correct_counts", 0) > 0:
                winner_id = top_user.get("_id")
                winner_score = top_user.get("correct_counts", 0)
                embed = discord.Embed(
                    title="14days game ended",
                    description=f"👑**Winner:** <@{winner_id}> score **{winner_score}**. ty for counting!",
                    color=discord.Color.gold()
                )
                await channel.send(embed=embed)
        except: continue

    leaderboard_collection.delete_many({})
    new_deadline = datetime.now(timezone.utc) + timedelta(days=14)
    system_collection.update_one({"_id": "global_tournament"}, {"$set": {"end_date": new_deadline}})
# ==============================================================================
# PART 5: CORE CHAT INTERCEPTOR & MEMORY-CACHED PARSER
# ==============================================================================
import time

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}! Lag-free tracking matrix initialized.')
    get_tournament_deadline()
    scheduler.add_job(check_and_announce_winners, IntervalTrigger(hours=1))
    scheduler.start()

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    current_channel_str = str(message.channel.id)

    # === C3 CHANNEL ROLE AUTOMATION PROCESSING ===
    if current_channel_str == c3 and message.embeds:
        if message.author.id not in [COUNTING_BOT_ID, CLASSIC_BOT_ID]:
            return

        embed = message.embeds[0] if isinstance(message.embeds, list) else message.embeds
        guild = message.guild
        member = None

        raw_text_name = ""
        if embed.title: raw_text_name = embed.title
        elif embed.author and embed.author.name: raw_text_name = embed.author.name

        if raw_text_name:
            cleaned_name = re.sub(r"(Stats for|'s Stats|'s stats|Stats of|stats)", "", raw_text_name, flags=re.IGNORECASE).strip()
            try:
                query_results = await guild.query_members(query=cleaned_name, limit=1)
                if query_results: member = query_results[0]
            except: pass

        if not member: return

        global_stats_text = ""
        for field in embed.fields:
            if "Global Stats" in field.name:
                global_stats_text = field.value
                break
        if not global_stats_text and embed.description:
            if "Global Stats" in embed.description: global_stats_text = embed.description

        if not global_stats_text: return

        if message.author.id == COUNTING_BOT_ID:
            match = re.search(r'Score:\s*(?:\*\*)?([\d,]+)(?:\*\*)?', global_stats_text)
            if match:
                score = int(match.group(1).replace(',', ''))
                target_role = None
                for min_v, max_v, name in STANDARD_TIERS:
                    if min_v <= score <= max_v:
                        target_role = name
                        break
                if target_role:
                    role = discord.utils.get(guild.roles, name=target_role)
                    if not role:
                        role = await guild.create_role(name=target_role, colour=discord.Colour.purple())
                        # Auto-unlock permission access down to 10000 score
                        if int(target_role) >= 10000 and c1:
                            target_ch = guild.get_channel(int(c1))
                            if target_ch: await target_ch.set_permissions(role, view_channel=True, send_messages=True)
                    removals = [r for r in member.roles if r.name in [t[2] for t in ALL_STANDARD_NAMES] and r.name != target_role]
                    if role not in member.roles:
                        if removals: await member.remove_roles(*removals)
                        await member.add_roles(role)

        elif message.author.id == CLASSIC_BOT_ID:
            match = re.search(r'Score:\s*(?:\*\*)?([\d,]+)(?:\*\*)?', global_stats_text)
            if match:
                score = int(match.group(1).replace(',', ''))
                target_role = None
                for min_v, max_v, name in CLASSIC_TIERS:
                    if min_v <= score <= max_v:
                        target_role = name
                        break
                if target_role:
                    role = discord.utils.get(guild.roles, name=target_role)
                    if not role:
                        role = await guild.create_role(name=target_role, colour=discord.Colour.blue())
                        # Auto-unlock permission access down to 10000c score
                        if int(target_role.replace('c','')) >= 10000 and c2:
                            target_ch = guild.get_channel(int(c2))
                            if target_ch: await target_ch.set_permissions(role, view_channel=True, send_messages=True)
                    removals = [r for r in member.roles if r.name in [t[2] for t in ALL_CLASSIC_NAMES] and r.name != target_role]
                    if role not in member.roles:
                        if removals: await member.remove_roles(*removals)
                        await member.add_roles(role)
        return

    # === GAME CHANNELS PROGRESSIVE COUNTING PROCESSING (C1 & C2) ===
    if current_channel_str not in COUNTING_CHANNELS: return
    if "You have used 1 guild save!" in message.content:
        try:
            await message.channel.set_permissions(message.guild.default_role, send_messages=False)
            await message.channel.send("🔒 **Channel Locked! wait... **.")
        except: pass
        return

    if message.author.bot: return
    content = message.content.strip()
    if content.startswith('r!'): return

    try:
        input_number = int(content)
        if str(input_number) != content: return
    except ValueError: return

    # INSTANT CACHE PROCESSING (Zero Internet Lag)
    cache = MEMORY_STREAKS[current_channel_str]
    
    # Auto-initialize baseline state if memory is empty
    if cache["current_count"] is None:
        cache["current_count"] = input_number - 1
        cache["last_user_id"] = None

    expected_number = cache["current_count"] + 1

    # Standard sequencing enforcement rules
    if input_number != expected_number or message.author.id == cache["last_user_id"]:
        # Sequence break: Reset memory cache baseline matching the mistake
        cache["current_count"] = input_number
        cache["last_user_id"] = message.author.id
        return

    # Commit memory validation benchmarks instantly
    cache["current_count"] = input_number
    cache["last_user_id"] = message.author.id

    # Award points seamlessly
    increment_global_score(message.author.id)

    # Fast Race Tracking Module
    race = races_collection.find_one({"_id": f"race_{current_channel_str}"})
    if race:
        if race.get("start_time") is None:
            races_collection.update_one({"_id": f"race_{current_channel_str}"}, {"$set": {"start_time": time.time()}})
        log_race_contribution(current_channel_str, message.author.id)


# ==============================================================================
# PART 6: COMPUTATION MODULES & CALCULATION ENGINE LOGIC
# ==============================================================================
def get_channel_and_guild(ctx_or_interaction):
    if isinstance(ctx_or_interaction, commands.Context):
        return ctx_or_interaction.channel, ctx_or_interaction.guild, ctx_or_interaction
    else:
        return ctx_or_interaction.channel, ctx_or_interaction.guild, ctx_or_interaction.response

async def run_logic(ctx_or_interaction):
    channel, guild, responder = get_channel_and_guild(ctx_or_interaction)
    channel_id_str = str(channel.id)
    if channel_id_str not in COUNTING_CHANNELS:
        await responder.send_message("❌ can only be initialized inside og and classic", ephemeral=True)
        return

    existing_race = races_collection.find_one({"_id": f"race_{channel_id_str}"})
    if existing_race:
        await responder.send_message("already running <3", ephemeral=True)
        return

    races_collection.insert_one({
        "_id": f"race_{channel_id_str}", "channel_id": channel_id_str,
        "start_time": None, "total_counts": 0, "players": {}
    })
    await responder.send_message(f"**race has begun in <#{channel_id_str}>!**")

async def yay_logic(ctx_or_interaction):
    channel, guild, responder = get_channel_and_guild(ctx_or_interaction)
    channel_id_str = str(channel.id)
    if channel_id_str not in COUNTING_CHANNELS: return

    race = races_collection.find_one({"_id": f"race_{channel_id_str}"})
    if not race:
        await responder.send_message("❌ no active race ", ephemeral=True)
        return

    start_time = race.get("start_time")
    if start_time is None:
        duration_hours = 0.0001
    else:
        total_seconds_elapsed = time.time() - float(start_time)
        duration_hours = max(total_seconds_elapsed / 3600.0, 0.0001)

    total_counts = race.get("total_counts", 0)
    final_pace = round(total_counts / duration_hours, 1)

    embed = discord.Embed(title=f"🛑 Race Finished — #{channel.name}", color=discord.Color.red())
    embed.description = f"**pace:** `{final_pace} counts/hr`\n**counts:** `{total_counts}`"
    
    players = race.get("players", {})
    mvp_list = []
    if players:
        sorted_players = sorted(players.items(), key=lambda item: item[1], reverse=True)
        for user_id, counts in sorted_players[:2]:
            mvp_list.append({"id": user_id, "score": counts})
        leaderboard_text = ""
        for index, (p_id, p_counts) in enumerate(sorted_players[:5]):
            leaderboard_text += f"`#{index+1}` <@{p_id}> — {p_counts} drops ({round(p_counts / duration_hours, 1)}/hr)\n"
        embed.add_field(name="Standings", value=leaderboard_text, inline=False)

    if total_counts > 0:
        top_races_collection.insert_one({
            "pace": final_pace, "total_counts": total_counts, "channel_name": channel.name,
            "mvp1_id": mvp_list[0]["id"] if len(mvp_list) > 0 else None,
            "mvp2_id": mvp_list[1]["id"] if len(mvp_list) > 1 else None,
            "timestamp": datetime.now(timezone.utc)
        })

    races_collection.delete_one({"_id": f"race_{channel_id_str}"})
    
    # Wipe the local memory cache baseline matching the end of the speed track session
    MEMORY_STREAKS[channel_id_str] = {"current_count": None, "last_user_id": None}
    
    if isinstance(ctx_or_interaction, commands.Context): await responder.send(embed=embed)
    else: await responder.send_message(embed=embed)

async def pace_logic(ctx_or_interaction):
    channel, guild, responder = get_channel_and_guild(ctx_or_interaction)
    active_races = list(races_collection.find())
    if not active_races:
        await responder.send_message("no active runs", ephemeral=True)
        return

    embed = discord.Embed(title="pace", color=discord.Color.teal())
    for race in active_races:
        ch_id = race["channel_id"]
        start_time = race.get("start_time")
        
        if start_time is None:
            current_pace = 0.0
        else:
            total_seconds_elapsed = time.time() - float(start_time)
            elapsed_hours = max(total_seconds_elapsed / 3600.0, 0.0001)
            current_pace = round(race.get("total_counts", 0) / elapsed_hours, 1)
        
        players = race.get("players", {})
        mvp_display = "None"
        if players:
            sorted_players = sorted(players.items(), key=lambda item: item[1], reverse=True)
            if len(sorted_players) >= 2:
                mvp_display = f"1. <@{sorted_players[0][0]}> ({sorted_players[0][1]} drops)\n2. <@{sorted_players[1][0]}> ({sorted_players[1][1]} drops)"
            else:
                mvp_display = f"1. <@{sorted_players[0][0]}> ({sorted_players[0][1]} drops)"

        field_value = f"• **Current Speed:** `{current_pace} counts/hr`\n• **drops:** `{race.get('total_counts', 0)}`\n• **Top 2 Counters:**\n{mvp_display}"
        channel_obj = bot.get_channel(int(ch_id))
        embed.add_field(name=f"🏁 Channel: #{channel_obj.name if channel_obj else ch_id}", value=field_value, inline=False)
        
    if isinstance(ctx_or_interaction, commands.Context): await responder.send(embed=embed)
    else: await responder.send_message(embed=embed)

async def toprun_logic(ctx_or_interaction):
    channel, guild, responder = get_channel_and_guild(ctx_or_interaction)
    if str(channel.id) in COUNTING_CHANNELS: return
    records = list(top_races_collection.find().sort("pace", -1).limit(10))
    embed = discord.Embed(title="Top 10 Fastest Runs", color=discord.Color.purple())

    if not records: embed.description = "no races yet!"
    else:
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for index, record in enumerate(records):
            rank = medals[index] if index < 3 else f"`#{index + 1}`"
            mvp1, mvp2 = record.get("mvp1_id"), record.get("mvp2_id")
            mvp_text = f"<@{mvp1}>" if mvp1 else "None"
            if mvp2: mvp_text += f" & <@{mvp2}>"
            leaderboard_text += f"{rank} **{record.get('pace', 0.0)}** — ({record.get('total_counts')}) | MVPs: {mvp_text}\n"
        embed.description = leaderboard_text

    if isinstance(ctx_or_interaction, commands.Context): await responder.send(embed=embed)
    else: await responder.send_message(embed=embed)

async def lb_logic(ctx_or_interaction):
    channel, guild, responder = get_channel_and_guild(ctx_or_interaction)
    if str(channel.id) in COUNTING_CHANNELS: return  
    top_users = list(leaderboard_collection.find().sort("correct_counts", -1).limit(10))
    timer = get_tournament_deadline()
    embed = discord.Embed(title="🏆 server leaderboard(14 days)", color=discord.Color.blue())
    
    if not top_users: embed.description = "is empty :("
    else:
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for index, user_data in enumerate(top_users):
            leaderboard_text += f"{medals[index] if index < 3 else f'`#{index + 1}`'} <@{user_data.get('_id')}> — {user_data.get('correct_counts')} total pts\n"
        embed.description = leaderboard_text

    end_date = timer["end_date"].replace(tzinfo=timezone.utc) if timer["end_date"].tzinfo is None else timer["end_date"]
    embed.set_footer(text=f"remaining: {max(0, (end_date - datetime.now(timezone.utc)).days)} Days")
    if isinstance(ctx_or_interaction, commands.Context): await responder.send(embed=embed)
    else: await responder.send_message(embed=embed)


# ==============================================================================
# PART 7: LEGACY TEXT COMMANDS ROUTING ENGINE
# ==============================================================================
@bot.command(name='run')
async def text_run(ctx): await run_logic(ctx)

@bot.command(name='yay')
async def text_yay(ctx): await yay_logic(ctx)

@bot.command(name='pace')
async def text_pace(ctx): await pace_logic(ctx)

@bot.command(name='toprun')
async def text_toprun(ctx): await toprun_logic(ctx)

@bot.command(name='lb')
async def text_lb(ctx): await lb_logic(ctx)

@bot.command(name='lock')
@commands.has_permissions(administrator=True)
async def text_lock(ctx):
    if str(ctx.channel.id) not in COUNTING_CHANNELS: return
    
    # 1. Lock base everyone role
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    
    # 2. Loop and override typing permissions for all standard and classic milestone role tags
    for tier in STANDARD_TIERS:
        role_name = tier[2]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role: await ctx.channel.set_permissions(role, send_messages=False)
        
    for tier in CLASSIC_TIERS:
        role_name = tier[2]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role: await ctx.channel.set_permissions(role, send_messages=False)
        
    await ctx.send("🔒 **Channel Locked!** wait...")

@bot.command(name='unlock')
@commands.has_permissions(administrator=True)
async def text_unlock(ctx):
    if str(ctx.channel.id) not in COUNTING_CHANNELS: return
    
    # 1. Reset everyone role base state
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    
    # 2. Restore individual permissions back to their active tier parameters
    for tier in STANDARD_TIERS:
        role_name = tier[2]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            # Re-unlock the channel only for users who are qualified (>= 25000) inside c1
            if int(role_name) >= 25000 and str(ctx.channel.id) == c1:
                await ctx.channel.set_permissions(role, view_channel=True, send_messages=True)
            else:
                await ctx.channel.set_permissions(role, overwrite=None)
                
    for tier in CLASSIC_TIERS:
        role_name = tier[2]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            val = int(role_name.replace('c',''))
            # Re-unlock the channel only for users who are qualified (>= 25000) inside c2
            if val >= 25000 and str(ctx.channel.id) == c2:
                await ctx.channel.set_permissions(role, view_channel=True, send_messages=True)
            else:
                await ctx.channel.set_permissions(role, overwrite=None)
                
    await ctx.send("🔓 **Channel Unlocked!**")

@bot.command(name='reset')
@commands.has_permissions(administrator=True)
async def text_reset(ctx):
    leaderboard_collection.delete_many({})
    new_deadline = datetime.now(timezone.utc) + timedelta(days=14)
    system_collection.update_one({"_id": "global_tournament"}, {"$set": {"end_date": new_deadline}}, upsert=True)
    await ctx.send("🔄 **game reset!**")
# ==============================================================================
# PART 8: NATIVE SLASH COMMANDS ARCHITECTURE MAP
# ==============================================================================
@bot.tree.command(name='run', description='starts race.')
async def slash_run(interaction: discord.Interaction): await run_logic(interaction)

@bot.tree.command(name='yay', description='stops the active race.')
async def slash_yay(interaction: discord.Interaction): await yay_logic(interaction)

@bot.tree.command(name='pace', description='running races.')
async def slash_pace(interaction: discord.Interaction): await pace_logic(interaction)

@bot.tree.command(name='toprun', description='top 10 fastest races.')
async def slash_toprun(interaction: discord.Interaction): await toprun_logic(interaction)

@bot.tree.command(name='lb', description='14day server leaderboard')
async def slash_lb(interaction: discord.Interaction): await lb_logic(interaction)

@bot.tree.command(name='lock', description='locks down')
@app_commands.checks.has_permissions(administrator=True)
async def slash_lock(interaction: discord.Interaction):
    if str(interaction.channel.id) not in COUNTING_CHANNELS:
        await interaction.response.send_message("❌ not here lol.", ephemeral=True)
        return
        
    await interaction.response.defer()
    # 1. Lock base everyone role
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    
    # 2. Loop and override typing permissions for all standard and classic milestone role tags via Slash
    for tier_info in STANDARD_TIERS:
        role_name = tier_info[2]
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role: await interaction.channel.set_permissions(role, send_messages=False)
        
    for tier_info in CLASSIC_TIERS:
        role_name = tier_info[2]
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role: await interaction.channel.set_permissions(role, send_messages=False)
        
    await interaction.followup.send("🔒 **Channel Locked!**")

@bot.tree.command(name='unlock', description='unlocks the counting channel')
@app_commands.checks.has_permissions(administrator=True)
async def slash_unlock(interaction: discord.Interaction):
    if str(interaction.channel.id) not in COUNTING_CHANNELS:
        await interaction.response.send_message("❌ not here", ephemeral=True)
        return
        
    await interaction.response.defer()
    # 1. Reset everyone role base state
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
    
    # 2. Restore individual view/send permissions back to their active tier parameters via Slash
    for tier_info in STANDARD_TIERS:
        role_name = tier_info[2]
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            if int(role_name) >= 25000 and str(interaction.channel.id) == c1:
                await interaction.channel.set_permissions(role, view_channel=True, send_messages=True)
            else:
                await interaction.channel.set_permissions(role, overwrite=None)
                
    for tier_info in CLASSIC_TIERS:
        role_name = tier_info[2]
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            val = int(role_name.replace('c',''))
            if val >= 25000 and str(interaction.channel.id) == c2:
                await interaction.channel.set_permissions(role, view_channel=True, send_messages=True)
            else:
                await interaction.channel.set_permissions(role, overwrite=None)
                
    await interaction.followup.send("🔓 **Channel Unlocked!**")

@bot.tree.command(name='reset', description='manually wipes the 14day game scoreboard and restarts yay.')
@app_commands.checks.has_permissions(administrator=True)
async def slash_reset(interaction: discord.Interaction):
    leaderboard_collection.delete_many({})
    new_deadline = datetime.now(timezone.utc) + timedelta(days=14)
    system_collection.update_one({"_id": "global_tournament"}, {"$set": {"end_date": new_deadline}}, upsert=True)
    await interaction.response.send_message("**game reset!** clean clean clean.")

bot.run(TOKEN)
