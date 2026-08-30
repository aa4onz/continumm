from variables import *
import run, end, pace, topruns, lb, lock, alt, reset

def register():
    bot.add_command(c.Command(run.exec, name='run'))
    bot.add_command(c.Command(end.exec, name='end'))
    bot.add_command(c.Command(pace.exec, name='pace'))
    bot.add_command(c.Command(topruns.exec, name='topruns'))
    bot.add_command(c.Command(lb.exec, name='lb'))
    bot.add_command(c.Command(lambda ctx: lock.exec(ctx, True), name='lock'))
    bot.add_command(c.Command(lambda ctx: lock.exec(ctx, False), name='unlock'))
    bot.add_command(c.Command(alt.exec, name='alt'))
    bot.add_command(c.Command(reset.exec, name='reset'))
  
