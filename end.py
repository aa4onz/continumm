import time
from datetime import datetime as dt, timezone as tz
from variables import *
from utils import ctx_parse

async def exec(tgt):
    chan, _, resp = ctx_parse(tgt)
    cid = str(chan.id)
    
    if cid not in ch: 
        return
        
    rc = db_rc.find_one({"_id": f"race_{cid}"})
    if not rc: 
        return await (resp.send("❌ no active race") if isinstance(tgt, c.Context) else resp.send_message("❌ no active race", ephemeral=True))
    
    n0 = rc.get("start_num")
    n1 = rc.get("last_num")
    t0 = rc.get("start_time")
    t1 = rc.get("last_time")
    
    # Calculate absolute count parameters
    cnt = (n1 - n0) if (n1 is not None and n0 is not None) else 0
    
    if t1 and t0 and (t1 - t0) > 0:
        hrs = (t1 - t0) / 3600.0
    else:
        hrs = 0.0001
        
    pace = round(cnt / hrs, 1) if cnt > 0 else 0.0
    
    time_bracket = f"(<t:{int(time.time())}:t>)"
    emb = d.Embed(
        title=f"Race Finished — #{chan.name} {time_bracket}", 
        color=d.Color.red(), 
        description=f"**pace:** `{pace:,} /hr`\n**counts:** `{cnt:,}`"
    )
    
    # Extract the first two unique users recorded in the database dictionary payload
    players_list = list(rc.get("players", {}).keys())
    mvp1 = str(players_list[0]) if len(players_list) > 0 else None
    mvp2 = str(players_list[1]) if len(players_list) > 1 else None
    
    if cnt > 0:
        db_top.insert_one({
            "pace": pace, 
            "total_counts": cnt, 
            "channel_name": chan.name, 
            "mvp1_id": mvp1, 
            "mvp2_id": mvp2, 
            "timestamp": dt.now(tz.utc)
        })
        
    db_rc.delete_one({"_id": f"race_{cid}"})
    cache[cid] = {"n": None, "u": None}
    
    await (resp.send(embed=emb) if isinstance(tgt, c.Context) else resp.send_message(embed=emb))
