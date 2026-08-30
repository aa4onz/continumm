from variables import *
from utils import ctx_parse

async def exec(tgt):
    ch, _, resp = ctx_parse(tgt)
    cid = str(ch.id)
    if cid not in ch:
        return await (resp.send("can only be initialized inside +1 and classic") if isinstance(tgt, c.Context) else resp.send_message("can only be initialized inside +1 and classic", ephemeral=True))
    if db_rc.find_one({"_id": f"race_{cid}"}):
        return await (resp.send("already running <3") if isinstance(tgt, c.Context) else resp.send_message("already running <3", ephemeral=True))
    db_rc.insert_one({"_id": f"race_{cid}", "channel_id": cid, "start_time": None, "total_counts": 0, "players": {}})
    await (resp.send(f"**race has begun in <#{cid}>!**") if isinstance(tgt, c.Context) else resp.send_message(f"**race has begun in <#{cid}>!**"))
  
