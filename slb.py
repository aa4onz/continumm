from variables import *
from utils import ctx_parse
import menus

async def exec(tgt):
    chan, _, resp = ctx_parse(tgt)
    if str(chan.id) in ch: 
        return
        
    uid = tgt.author.id if isinstance(tgt, c.Context) else tgt.user.id
    
    # 1. Fetch top 100 entries matching the sorting style of your 14-day script
    raw_data = list(db_alltime.find().sort("all_time_counts", -1).limit(100))
    
    # 2. Format the list elements dynamically so menus.py can read the numerical fields
    formatted_data = []
    for row in raw_data:
        formatted_data.append({
            "_id": row["_id"],
            "correct_counts": row.get("all_time_counts", 0)  # Map to correct_counts for menus.py compatibility
        })
    
    # 3. Build the pagination structure using your matching engine framework
    v = menus.create_paginator(
        v=formatted_data, 
        h="server leaderboard(all time)", 
        c=d.Color.green(), 
        is_lb=True, 
        author_id=uid
    )
    
    await (resp.send(embed=v.build_embed(), view=v) if isinstance(tgt, c.Context) else resp.send_message(embed=v.build_embed(), view=v))
