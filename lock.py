from variables import *
from utils import ctx_parse

async def exec(tgt, status=True):
    chan, guild, resp = ctx_parse(tgt)
    cid = str(chan.id)
    if cid not in ch: 
        return
        
    if isinstance(tgt, d.Interaction): 
        await resp.defer()
        
    if status:
        # 🔒 LOCK DOWN TIMELINE ACTIONS
        await chan.set_permissions(guild.default_role, send_messages=False)
        
        current_tiers = t if cid == c1 else ct
        for _, _, rname in current_tiers:
            role_obj = d.utils.get(guild.roles, name=rname)
            if role_obj:
                await chan.set_permissions(role_obj, send_messages=False)
    else:
        # 🔓 UNLOCK GAME CHANNELS ACTIONS
        await chan.set_permissions(guild.default_role, send_messages=False)
        
        current_tiers = t if cid == c1 else ct
        for _, _, rname in current_tiers:
            role_obj = d.utils.get(guild.roles, name=rname)
            if role_obj:
                val_num = int(rname.replace('c','').replace(',',''))
                if val_num >= 10000:
                    await chan.set_permissions(role_obj, view_channel=True, send_messages=True)
                else:
                    await chan.set_permissions(role_obj, overwrite=None)

    # 3. 🛡️ WHITELIST EXTERNAL SERVICE BOTS SO THEY NEVER GET LOCKED OUT
    # FIX: Add your third bot's exact user account ID right inside this array!
    for bid in [b1, b2, 989473317683617872]: # Replace 1111111111111111111 with your other bot's real ID
        bot_member = guild.get_member(bid)
        if bot_member: 
            await chan.set_permissions(bot_member, view_channel=True, send_messages=True, add_reactions=True)
            
    msg = "channel locked!" if status else "channel unlocked!"
    await (chan.send(msg) if isinstance(tgt, c.Context) else resp.followup.send(msg))
