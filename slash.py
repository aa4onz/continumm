from variables import *
from discord import app_commands
import run, end, pace, topruns, lb, lock, alt, reset, cn, slb

def register():
    # --- PUBLIC COMMANDS ---
    @bot.tree.command(name='run', description='start race')
    async def s_run(i): await run.exec(i)
    
    @bot.tree.command(name='end', description='end the active race and calculate the final pace')
    async def s_end(i): await end.exec(i)
    
    @bot.tree.command(name='pace', description='check the current pace')
    async def s_pace(i): await pace.exec(i)
    
    @bot.tree.command(name='topruns', description='view the leaderboard of the top 100 fastest races')
    async def s_top(i): await topruns.exec(i)
    
    @bot.tree.command(name='lb', description='view the 14day server leaderboard')
    async def s_lb(i): await lb.exec(i)

    @bot.tree.command(name='slb', description='view the server all time leaderboard')  # 👈 FIXED: Activated as /slb
    async def s_slb(i): await slb.exec(i)
    
    # --- ADMIN LOCKED COMMANDS (HIDDEN FROM MEMBERS) ---
    @bot.tree.command(name='lock', description='lock the counting channel')
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def s_lock(i): await lock.exec(i, True)
    
    @bot.tree.command(name='unlock', description='unlock the counting channel')
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def s_unlock(i): await lock.exec(i, False)
    
    @bot.tree.command(name='reset', description='reset the 14-day scoreboard and dates')
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def s_reset(i): await reset.exec(i)
    
    @bot.tree.command(name='alt', description='link a secondary alternate account to a primary main user profile')
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def s_alt(i, m: d.Member, a: d.Member): await alt.exec(i, m, a)
    
    @bot.tree.command(name='cn', description='set a custom fallback text username for members who left the server')
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def s_cn(i, user_id: str, custom_name: str): await cn.exec(i, user_id, custom_name=custom_name)
