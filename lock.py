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
        # 1. Lock down the base everyone server role
        await chan.set_permissions(guild.default_role, send_messages=False)
        
        # 2. Freeze access for all custom tier milestone roles in this channel
        current_tiers = t if cid == c1 else ct
        for _, _, rname in current_tiers:
            role_obj = d.utils.get(guild.roles, name=rname)
            if role_obj:
                await chan.set_permissions(role_obj, send_messages=False)
                
        # 3. FIX: Lock down the specific role named "alt" during lockdown
        alt_role = d.utils.get(guild.roles, name="alt")
        if alt_role:
            await chan.set_permissions(alt_role, send_messages=False)
    else:
        # 🔓 UNLOCK GAME CHANNELS ACTIONS
        # 1. Keep base everyone role LOCKED down securely as requested
        await chan.set_permissions(guild.default_role, send_messages=False)
        
        # 2. Restore access dynamically to the correct channel milestone array track
        current_tiers = t if cid == c1 else ct
        for _, _, rname in current_tiers:
            role_obj = d.utils.get(guild.roles, name=rname)
            if role_obj:
                val_num = int(rname.replace('c','').replace(',',''))
                if val_num >= 10000:
                    await chan.set_permissions(role_obj, view_channel=True, send_messages=True)
                else:
                    await chan.set_permissions(role_obj, overwrite=None)
                    
        # 3. FIX: Restore access for the specific role named "alt" on unlock
        alt_role = d.utils.get(guild.roles, name="alt")
        if alt_role:
            await chan.set_permissions(alt_role, view_channel=True, send_messages=True)

    # 4. Always whitelist external counting bots so they never get locked out
    for bid in [b1, b2, 989473317683617872]: # Replace with your real third helper bot ID
        bot_member = guild.get_member(bid)
        if bot_member: 
            await chan.set_permissions(bot_member, view_channel=True, send_messages=True, add_reactions=True)
            
    msg = "⚠️ **Channel Locked!** Counting frozen by administrator." if status else "✅ **Channel Unlocked!** Progress counting lines restored."
    await (chan.send(msg) if isinstance(tgt, c.Context) else resp.followup.send(msg))
