from variables import *
import run, end, pace, topruns, lb, lock, alt, reset

def register():
    @bot.tree.command(name='run')
    async def s_run(i): await run.exec(i)
    
    @bot.tree.command(name='end')
    async def s_end(i): await end.exec(i)
    
    @bot.tree.command(name='pace')
    async def s_pace(i): await pace.exec(i)
    
    @bot.tree.command(name='topruns')
    async def s_top(i): await topruns.exec(i)
    
    @bot.tree.command(name='lb')
    async def s_lb(i): await lb.exec(i)
    
    @bot.tree.command(name='lock')
    async def s_lock(i): await lock.exec(i, True)
    
    @bot.tree.command(name='unlock')
    async def s_unlock(i): await lock.exec(i, False)
    
    @bot.tree.command(name='reset')
    async def s_reset(i): await reset.exec(i)
    
    @bot.tree.command(name='alt')
    async def s_alt(i, m: d.Member, a: d.Member): await alt.exec(i, m, a)
      
