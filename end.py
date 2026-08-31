from variables import *
from utils import ctx_parse

async def exec(tgt):
    chan, _, resp = ctx_parse(tgt)
    cid = str(chan.id)
    if cid not in ch: return
    rc = db_rc.find_one({"_id": f"race_{cid}"})
    if not rc: return await (resp.send("❌ no active race") if isinstance(tgt, c.Context) else resp.send_message("❌ no active race", ephemeral=True))
    t0 = rc.get("start_time")
    hrs = max((time.time() - float(t0)) / 3600.0, 0.0001) if t0 else 0.0001
    cnt = rc.get("total_counts", 0)
    pace = round(cnt / hrs, 1)
    
    # FIX: Added the missing client angle bracket wrappers around the finishing time log
    time_bracket = f"(<t:{int(time.time())}:t>)"
    emb = d.Embed(title=f"Race Finished — #{chan.name} {time_bracket}", color=d.Color.red(), description=f"**pace:** `{pace} /hr`\n**counts:** `{cnt}`")
    
    sorted_players = sorted(rc.get("players", {}).items(), key=lambda x: x[1], reverse=True)
    mvps = [uid for uid, _ in sorted_players[:2]]
    
    if cnt > 0:
        db_top.insert_one({
            "pace": pace, 
            "total_counts": cnt, 
            "channel_name": chan.name, 
            "mvp1_id": str(mvps[0]) if len(mvps) > 0 else None, 
            "mvp2_id": str(mvps[1]) if len(mvps) > 1 else None, 
            "timestamp": dt.now(tz.utc)
        })
    db_rc.delete_one({"_id": f"race_{cid}"})
    cache[cid] = {"n": None, "u": None}
    await (resp.send(embed=emb) if isinstance(tgt, c.Context) else resp.send_message(embed=emb))
