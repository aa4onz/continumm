import time
from variables import *
from utils import ctx_parse

async def exec(tgt):
    _, _, resp = ctx_parse(tgt)
    active = list(db_rc.find())
    
    if not active: 
        return await (resp.send("no active run") if isinstance(tgt, c.Context) else resp.send_message("no active run", ephemeral=True))
        
    emb = d.Embed(title="pace", color=d.Color.teal())
    for r in active:
        n0 = r.get("start_num")
        n1 = r.get("last_num")
        t0 = r.get("start_time")
        t1 = r.get("last_time")
        
        # Determine exact count delta
        total_counts = (n1 - n0) if (n1 is not None and n0 is not None) else 0
        
        # Calculate dynamic time window down to milliseconds
        if t1 and t0 and (t1 - t0) > 0:
            hrs = (t1 - t0) / 3600.0
        else:
            hrs = 0.0001
            
        pace = round(total_counts / hrs, 1) if total_counts > 0 else 0.0
        
        # Fetch the active player names who joined the run
        players = r.get("players", {})
        player_names = []
        for p_id in list(players.keys())[:5]: # Shows up to 5 unique participants
            obj = bot.get_user(int(p_id))
            player_names.append(obj.name if obj else f"User-{p_id}")
            
        txt = ", ".join(player_names) if player_names else "None"
        
        c_obj = bot.get_channel(int(r["channel_id"]))
        emb.add_field(
            name=f"Channel: #{c_obj.name if c_obj else r['channel_id']}", 
            value=f"• **Speed:** `{pace:,} /hr`\n• **counts:** `{total_counts:,}`\n• **Active Users:** {txt}", 
            inline=False
        )
        
    await (resp.send(embed=emb) if isinstance(tgt, c.Context) else resp.send_message(embed=emb))
