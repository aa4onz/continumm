from discord.ext import commands
from variables import *
from utils import ctx_parse

async def exec(ctx):
    # Security lock to verify the user is a server administrator
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ **Error:** Only server administrators can use this command.", delete_after=5)
        return

    # Block running inside game tracking channels to eliminate layout spam loops
    if str(ctx.channel.id) in ch: 
        return

    try:
        # 1. Read current live 14-day scores
        active_scores = list(db_lb.find())
        if not active_scores:
            return await ctx.send("❌ **Migration skipped:** No active players found in the 14-day data.")
            
        migrated_count = 0
        for player in active_scores:
            uid = player.get("_id")
            current_counts = player.get("correct_counts", 0)
            
            if current_counts > 0:
                # 2. Seed or add the values into your persistent all-time collection
                db_alltime.update_one(
                    {"_id": uid},
                    {"$set": {"all_time_counts": current_counts}},
                    upsert=True
                )
                migrated_count += 1
                
        await ctx.send(f"✅ **Migration Success:** Seeded **{migrated_count}** active players into the all-time leaderboard collection!")
        
    except Exception as e:
        await ctx.send(f"❌ **Critical Error during Migration:** `{e}`")

# --- AUTO PREFIX REGISTRATION LAYER ---
# This executes automatically when main.py boots and imports your modules!
cmd_migrate = commands.Command(exec, name='migrate')
bot.add_command(cmd_migrate)
