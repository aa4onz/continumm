from variables import *
from utils import deadline

async def check_winners():
    dl = deadline().get("end_date")
    if dt.now(tz.utc) < (dl.replace(tzinfo=tz.utc) if dl.tzinfo is None else dl): return
    top = db_lb.find_one(sort=[("correct_counts", -1)])
    for cid in ch:
        ch_obj = bot.get_channel(int(cid))
        if ch_obj and top and top.get("correct_counts", 0) > 0:
            await ch_obj.send(embed=d.Embed(title="14days game ended", description=f"**Winner:** <@{top.get('_id')}> counts **{top.get('correct_counts')}**.", color=d.Color.gold()))
    db_lb.delete_many({})
    db_sys.update_one({"_id": "global_tournament"}, {"$set": {"end_date": dt.now(tz.utc) + td(days=14)}})
  
