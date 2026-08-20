import os
import discord
from discord.ext import commands
from pymongo import MongoClient
import certifi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="r!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

c1 = str(os.getenv('c1')).strip()
c2 = str(os.getenv('c2')).strip()
COUNTING_CHANNELS = [c1, c2]

try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client["counting_bot_db"]
    leaderboard_collection = db["leaderboard"]       # 14-Day Global Scores
    system_collection = db["system_state"]           # Global tournament timer
    races_collection = db["active_races"]             # Live racing contexts
    top_races_collection = db["top_races"]           # Permanent Top 10 Records
    print(f"Connected to MongoDB Atlas! Tracking channels: {COUNTING_CHANNELS}")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

scheduler = AsyncIOScheduler()

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
            if not channel:
                continue

            if top_user and top_user.get("correct_counts", 0) > 0:
                winner_id = top_user.get("_id")
                winner_score = top_user.get("correct_counts", 0)
                
                embed = discord.Embed(
                    title="🎉 Tournament Ended! 🎉",
                    description=f"The 14-day global counting cycle is complete!\n\n👑 **Global Winner:** <@{winner_id}> with a total of **{winner_score}** correct counts combined across channels!",
                    color=discord.Color.gold()
                )
                await channel.send(embed=embed)
            else:
                await channel.send("⏳ The 14-day cycle ended, but nobody participated! Starting a new round.")
        except Exception:
            continue

    leaderboard_collection.delete_many({})
    new_deadline = datetime.now(timezone.utc) + timedelta(days=14)
    system_collection.update_one(
        {"_id": "global_tournament"},
        {"$set": {"end_date": new_deadline}}
    )

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}! Operational with automatic emergency channel locking features.')
    get_tournament_deadline()
    scheduler.add_job(check_and_announce_winners, IntervalTrigger(hours=1))
    scheduler.start()

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    current_channel_id_str = str(message.channel.id)
    if current_channel_id_str not in COUNTING_CHANNELS:
        return

    # Check if a premium counting bot sent the guild save alert text anywhere in the channel
    # We do NOT ignore bots here so we can see the save message sent by other bots
    if "You have used 1 guild save!" in message.content:
        try:
            # Overwrite everyone permission to lock the room instantly
            await message.channel.set_permissions(message.guild.default_role, send_messages=False)
            await message.channel.send("🔒 **Channel Locked!** A guild save was used. Please contact an Administrator to review and unlock (`r!unlock`).")
        except Exception as e:
            print(f"Failed to lock channel: {e}")
        return

    if message.author.bot:
        return

    content = message.content.strip()

    if content.startswith('r!'):
        return

    try:
        input_number = int(content)
        if str(input_number) != content:
            return
    except ValueError:
        return

    channel = message.channel
    previous_number = 0
    last_user_id = None

    async for msg in channel.history(limit=20):
        if msg.id == message.id:
            continue
        if msg.author.bot:
            continue

        msg_content = msg.content.strip()
        try:
            previous_number = int(msg_content)
            if str(previous_number) == msg_content:
                last_user_id = msg.author.id
                break
        except ValueError:
            continue

    expected_number = previous_number + 1

    if message.author.id == last_user_id:
        return

    if input_number != expected_number:
        return

    increment_global_score(message.author.id)

    race = races_collection.find_one({"_id": f"race_{current_channel_id_str}"})
    if race:
        log_race_contribution(current_channel_id_str, message.author.id)
# ==============================================================================
# RACING & TOURNAMENT COMMAND ENGINE (Prefix: r!)
# ==============================================================================

@bot.command(name='race')
async def start_race(ctx):
    """Starts a clean, local speed track session isolated to the active channel."""
    channel_id_str = str(ctx.channel.id)
    if channel_id_str not in COUNTING_CHANNELS:
        await ctx.send("❌ Racing tracks can only be initialized inside designated counting channels.")
        return

    existing_race = races_collection.find_one({"_id": f"race_{channel_id_str}"})
    if existing_race:
        await ctx.send("🏁 A race track session is already running inside this channel! Type `r!pace` to view performance metrics.")
        return

    races_collection.insert_one({
        "_id": f"race_{channel_id_str}",
        "channel_id": channel_id_str,
        "start_time": datetime.now(timezone.utc),
        "total_counts": 0,
        "players": {}
    })
    await ctx.send(f"🟢 **The Race has officially begun in <#{channel_id_str}>!** Drop sequential numbers fast to increase your counts/hr speed track!")


@bot.command(name='stop')
async def stop_race(ctx):
    """Stops the active room's track session and records its pace. Renders the top two MVPs."""
    channel_id_str = str(ctx.channel.id)
    if channel_id_str not in COUNTING_CHANNELS:
        return

    race = races_collection.find_one({"_id": f"race_{channel_id_str}"})
    if not race:
        await ctx.send("❌ There is no active race running inside this channel to stop.")
        return

    start_time = race["start_time"].replace(tzinfo=timezone.utc)
    duration_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600.0
    duration_hours = max(duration_hours, 0.0001) 
    
    total_counts = race.get("total_counts", 0)
    final_pace = round(total_counts / duration_hours, 1)

    embed = discord.Embed(title=f"🛑 Race Finished — #{ctx.channel.name}", color=discord.Color.red())
    embed.description = f"**Final Room Pace:** `{final_pace} counts/hr`\n**Total Numbers Dropped:** `{total_counts}`"
    
    players = race.get("players", {})
    mvp_list = []
    
    if players:
        # Sort players by their counts descending to find the top two counters
        sorted_players = sorted(players.items(), key=lambda item: item[1], reverse=True)
        
        # Pull the top 2 users safely
        for user_id, counts in sorted_players[:2]:
            mvp_list.append({"id": user_id, "score": counts})
            
        leaderboard_text = ""
        for index, (p_id, p_counts) in enumerate(sorted_players[:5]):
            p_pace = round(p_counts / duration_hours, 1)
            leaderboard_text += f"`#{index+1}` <@{p_id}> — {p_counts} drops ({p_pace}/hr)\n"
        embed.add_field(name="🏆 Contributor Standings", value=leaderboard_text, inline=False)

    # Save to permanent history records
    if total_counts > 0:
        top_races_collection.insert_one({
            "pace": final_pace,
            "total_counts": total_counts,
            "channel_name": ctx.channel.name,
            "mvp1_id": mvp_list[0]["id"] if len(mvp_list) > 0 else None,
            "mvp2_id": mvp_list[1]["id"] if len(mvp_list) > 1 else None,
            "timestamp": datetime.now(timezone.utc)
        })

    races_collection.delete_one({"_id": f"race_{channel_id_str}"})
    await ctx.send(embed=embed)


@bot.command(name='pace')
async def view_pace(ctx):
    """Displays real-time speed track performance for live running races, showing up to two MVPs."""
    active_races = list(races_collection.find())
    
    if not active_races:
        await ctx.send("ℹ️ No active races are running right now. Type `r!race` inside a counting channel to start one!")
        return

    embed = discord.Embed(title="⚡ Live Race Track Pace Metrics", color=discord.Color.teal())
    
    for race in active_races:
        ch_id = race["channel_id"]
        start_time = race["start_time"].replace(tzinfo=timezone.utc)
        
        elapsed_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600.0
        elapsed_hours = max(elapsed_hours, 0.0001) 
        
        total_counts = race.get("total_counts", 0)
        current_pace = round(total_counts / elapsed_hours, 1)
        
        players = race.get("players", {})
        mvp_display = "None"
        
        if players:
            sorted_players = sorted(players.items(), key=lambda item: item[1], reverse=True)
            if len(sorted_players) >= 2:
                mvp_display = f"1. <@{sorted_players[0][0]}> ({sorted_players[0][1]} drops)\n2. <@{sorted_players[1][0]}> ({sorted_players[1][1]} drops)"
            else:
                mvp_display = f"1. <@{sorted_players[0][0]}> ({sorted_players[0][1]} drops)"

        field_value = (
            f"• **Current Speed:** `{current_pace} counts/hr`\n"
            f"• **Total Drops:** `{total_counts}`\n"
            f"• **Top 2 Counters:**\n{mvp_display}"
        )
        
        channel_obj = bot.get_channel(int(ch_id))
        ch_name = channel_obj.name if channel_obj else f"ID: {ch_id}"
        embed.add_field(name=f"🏁 Channel: #{ch_name}", value=field_value, inline=False)
        
    await ctx.send(embed=embed)


@bot.command(name='topbox')
async def view_top_races(ctx):
    """Displays a permanent high-score board showing the Top 10 fastest races in server history with two MVPs."""
    if str(ctx.channel.id) in COUNTING_CHANNELS:
        return

    records = list(top_races_collection.find().sort("pace", -1).limit(10))

    embed = discord.Embed(title="🏆 All-Time Top 10 Fastest Races Leaderboard", color=discord.Color.purple())

    if not records:
        embed.description = "No completed races have been logged in server history yet!"
    else:
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for index, record in enumerate(records):
            pace = record.get("pace", 0.0)
            counts = record.get("total_counts", 0)
            ch_name = record.get("channel_name", "unknown")
            mvp1 = record.get("mvp1_id")
            mvp2 = record.get("mvp2_id")
            
            rank = medals[index] if index < 3 else f"`#{index + 1}`"
            
            mvp_text = f"<@{mvp1}>" if mvp1 else "None"
            if mvp2:
                mvp_text += f" & <@{mvp2}>"
                
            leaderboard_text += f"{rank} **{pace} counts/hr** — #{ch_name} ({counts} drops) | MVPs: {mvp_text}\n"
        embed.description = leaderboard_text

    await ctx.send(embed=embed)


@bot.command(name='unlock')
@commands.has_permissions(administrator=True)
async def unlock_channel(ctx):
    """Admin command to safely unlock a counting channel after an emergency guild save lockdown."""
    if str(ctx.channel.id) not in COUNTING_CHANNELS:
        await ctx.send("❌ This command can only be used inside a designated counting channel.")
        return
        
    try:
        # Restore everyone's view and message sending capabilities
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send("🔓 **Channel Unlocked!** Users can resume counting normally.")
    except Exception as e:
        await ctx.send(f"❌ Failed to reset permissions: {e}")


@bot.command(name='leaderboard')
async def leaderboard(ctx):
    if str(ctx.channel.id) in COUNTING_CHANNELS:
        return  

    top_users = list(leaderboard_collection.find().sort("correct_counts", -1).limit(10))
    timer = get_tournament_deadline()
    
    embed = discord.Embed(title="🏆 Server Global Counting Leaderboard", color=discord.Color.blue())
    
    if not top_users:
        embed.description = "The leaderboard is empty for this cycle."
    else:
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for index, user_data in enumerate(top_users):
            user_id = user_data.get("_id")
            counts = user_data.get("correct_counts", 0)
            rank = medals[index] if index < 3 else f"`#{index + 1}`"
            leaderboard_text += f"{rank} <@{user_id}> — {counts} total pts\n"
        embed.description = leaderboard_text

    end_date = timer["end_date"]
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
        
    time_left = end_date - datetime.now(timezone.utc)
    days_left = max(0, time_left.days)
    
    embed.set_footer(text=f"Time remaining in tournament: {days_left} Days")
    await ctx.send(embed=embed)

bot.run(TOKEN)
