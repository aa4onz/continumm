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
        t0 = r.get("start_time")
        hrs = max((time.time() - float(t0)) / 3600.0, 0.0001) if t0 else 0.0001
        
        sp = sorted(r.get("players", {}).items(), key=lambda x: x[1], reverse=True)
        
        # --- FIX: Fetch real username strings instead of raw un-cached <@ID> tags ---
        txt = "None"
        if sp:
            p1_id = int(sp[0][0])
            obj1 = bot.get_user(p1_id)
            name1 = obj1.name if obj1 else f"User-{p1_id}"
            txt = f"1. {name1} ({sp[0][1]:,} counts)"
            
        if len(sp) >= 2: 
            p2_id = int(sp[1][0])
            obj2 = bot.get_user(p2_id)
            name2 = obj2.name if obj2 else f"User-{p2_id}"
            txt += f"\n2. {name2} ({sp[1][1]:,} counts)"
            
        c_obj = bot.get_channel(int(r["channel_id"]))
        emb.add_field(
            name=f"Channel: #{c_obj.name if c_obj else r['channel_id']}", 
            value=f"• **Speed:** `{round(r.get('total_counts',0)/hrs, 1):,} /hr`\n• **counts:** `{r.get('total_counts',0):,}`\n• **Top:**\n{txt}", 
            inline=False
        )
        
    await (resp.send(embed=emb) if isinstance(tgt, c.Context) else resp.send_message(embed=emb))
