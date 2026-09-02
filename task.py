from variables import *
from utils import deadline

async def check_winners():
    dl = deadline().get("end_date")
    if dt.now(tz.utc) < (dl.replace(tzinfo=tz.utc) if dl.tzinfo is None else dl): return
    
    top = db_lb.find_one(
        {"_id": {"$ne": "1399789300387942621"}}, 
        sort=[("correct_counts", -1)]
    )
    
    for cid in ch:
        ch_obj = bot.get_channel(int(cid))
        if ch_obj and top and top.get("correct_counts", 0) > 0:
            winner_id = top.get('_id')
            
            # Formats your exact phrase with the native member highlight link
            msg_text = f" <@{winner_id}> has won a save slot! happy counting 🎉"
            await ch_obj.send(msg_text)
            
    db_lb.delete_many({})
    db_sys.update_one({"_id": "global_tournament"}, {"$set": {"end_date": dt.now(tz.utc) + td(days=14)}})
