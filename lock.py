from variables import *
from utils import ctx_parse

async def exec(tgt, status=True):
    chan, guild, resp = ctx_parse(tgt)
    cid = str(chan.id)
    if cid not in ch: return
    if isinstance(tgt, d.Interaction): await resp.defer()
    await chan.set_permissions(guild.default_role, send_messages=False)
    for mn, mx, name in (t if cid == c1 else ct):
        r = d.utils.get(guild.roles, name=name)
        if r: await chan.set_permissions(r, overwrite=(None if (not status and int(name.replace('c','').replace(',','')) >= 10000) else d.PermissionOverwrite(send_messages=False)))
    for bid in [b1, b2]:
        m = guild.get_member(bid)
        if m: await chan.set_permissions(m, view_channel=True, send_messages=True, add_reactions=True)
    msg = "**Channel Locked!** wait..." if status else "**Channel Unlocked**"
    await (chan.send(msg) if isinstance(tgt, c.Context) else resp.followup.send(msg))
