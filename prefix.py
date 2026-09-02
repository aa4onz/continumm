from variables import *
from discord.ext import commands
import run, end, pace, topruns, lb, lock, alt, reset, cn, slb

def register():
    bot.add_command(c.Command(run.exec, name='run'))
    bot.add_command(c.Command(end.exec, name='end'))
    bot.add_command(c.Command(pace.exec, name='pace'))
    bot.add_command(c.Command(topruns.exec, name='topruns'))
    bot.add_command(c.Command(lb.exec, name='lb'))
    bot.add_command(c.Command(serverlb.exec, name='slb'))
    
    # --- ADMIN LOCKED TEXT COMMANDS ---
    cmd_alt = c.Command(alt.exec, name='alt')
    cmd_alt.add_check(commands.has_permissions(administrator=True).predicate)
    bot.add_command(cmd_alt)
    
    cmd_reset = c.Command(reset.exec, name='reset')
    cmd_reset.add_check(commands.has_permissions(administrator=True).predicate)
    bot.add_command(cmd_reset)
    
    cmd_cn = c.Command(cn.exec, name='cn')
    cmd_cn.add_check(commands.has_permissions(administrator=True).predicate)
    bot.add_command(cmd_cn)
    
    async def cmd_lock(ctx): 
        await lock.exec(ctx, True)
    c_lock = c.Command(cmd_lock, name='lock')
    c_lock.add_check(commands.has_permissions(administrator=True).predicate)
    bot.add_command(c_lock)
    
    async def cmd_unlock(ctx): 
        await lock.exec(ctx, False)
    c_unlock = c.Command(cmd_unlock, name='unlock')
    c_unlock.add_check(commands.has_permissions(administrator=True).predicate)
    bot.add_command(c_unlock)
