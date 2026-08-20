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

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

# Safely parse strings from Railway variables into integers for Discord compatibility
try:
    c1 = int(os.getenv('c1'))
    c2 = int(os.getenv('c2'))
    COUNTING_CHANNELS = [c1, c2]
except (TypeError, ValueError) as e:
    print(f"Error parsing channel environment variables c1 or c2: {e}")
    COUNTING_CHANNELS = []

try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client["counting_bot_db"]
    leaderboard_collection = db["leaderboard"]  # Stores combined global user scores
    system_collection = db["system_state"]       # Stores global tournament timer
    print("Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

scheduler = AsyncIOScheduler()

def get_tournament_deadline():
    """Fetches or initializes the global 14-day tournament timer using timezone-aware UTC."""
    timer = system_collection.find_one({"_id": "global_tournament"})
    if not timer:
        deadline = datetime.now(timezone.utc) + timedelta(days=14)
        new_timer = {"_id": "global_tournament", "end_date": deadline}
        system_collection.insert_one(new_timer)
        return new_timer
    return timer

def increment_global_score(user_id):
    """Combines points globally! Adds +1 to a user's total score regardless of which channel they used."""
    leaderboard_collection.update_one(
        {"_id": user_id},
        {"$inc": {"correct_counts": 1}},
        upsert=True
    )

async def check_and_announce_winners():
    """Checks the global 14-day timer and announces the absolute winner to both channels."""
    timer = get_tournament_deadline()
    deadline = timer.get("end_date")
    
    # Ensure deadline from DB has UTC timezone info attached
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) < deadline:
        return

    # Find the top player across the whole server
    top_user = leaderboard_collection.find_one(sort=[("correct_counts", -1)])

    # Broadcast the winner text announcement to BOTH counting channels
    for channel_id in COUNTING_CHANNELS:
        channel = bot.get_channel(channel_id)
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

    # WIPE EVERYTHING FOR THE RESET
    leaderboard_collection.delete_many({})  # Clear total user points
        
    # Calculate and set the next 14-day deadline
    new_deadline = datetime.now(timezone.utc) + timedelta(days=14)
    system_collection.update_one(
        {"_id": "global_tournament"},
        {"$set": {"end_date": new_deadline}}
    )

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} tracking total scores natively across history logs!')
    get_tournament_deadline()
    scheduler.add_job(check_and_announce_winners, IntervalTrigger(hours=1))
    scheduler.start()

@bot.event
async def on_message(message):
    # Route global commands normally if they happen outside counting channels
    if message.channel.id not in COUNTING_CHANNELS:
        await bot.process_commands(message)
        return

    if message.author.bot:
        return

    content = message.content.strip()

    try:
        input_number = int(content)
        if str(input_number) != content:
            return
    except ValueError:
        return

    channel = message.channel
    previous_number = 0
    last_user_id = None

    # Dynamically query the last two entries to check historical chat context
    # history[0] is the message just sent; history[1] is the one before it
    history = [msg async for msg in channel.history(limit=2)]
    
    if len(history) > 1:
        last_msg = history[1]
        last_user_id = last_msg.author.id
        try:
            previous_number = int(last_msg.content.strip())
        except ValueError:
            # If text directly above isn't a plain integer, sequence fell back to a clean start
            previous_number = 0

    expected_number = previous_number + 1

    # Rule 1: No double counting inside the SAME channel (Fails silently)
    if message.author.id == last_user_id:
        return

    # Rule 2: Sequence check for this channel (Fails silently)
    if input_number != expected_number:
        return

    # Valid step: User successfully matched the sequence! Log their global points
    increment_global_score(message.author.id)


@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """Displays the top 10 global leaderboard combining both channels."""
    if ctx.channel.id in COUNTING_CHANNELS:
        return  # Keep counting channels completely silent

    # Fetch top 10 users across the entire server
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

    # Show remaining days in the global cycle with accurate timezone-aware math
    end_date = timer["end_date"]
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
        
    time_left = end_date - datetime.now(timezone.utc)
    days_left = max(0, time_left.days)
    
    embed.set_footer(text=f"Time remaining in tournament: {days_left} Days")
    await ctx.send(embed=embed)

bot.run(TOKEN)
