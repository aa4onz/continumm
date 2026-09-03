from variables import *
from utils import deadline

async def check_winners():
    dl = deadline().get("end_date")
    if not dl: return
    
    # Cleanly normalize date formats to account for missing time zone markers
    end_time = dl.replace(tzinfo=tz.utc) if dl.tzinfo is None else dl
    
    # FIX: Change strict window checking to see if current time is GREATER THAN OR EQUAL to deadline
    # This guarantees execution even if the bot is 30 minutes, 5 hours, or days overdue!
    if dt.now(tz.utc) < end_time: 
        return
        
    print("[SYSTEM] Tournament deadline reached or passed. Starting automated settlement loop...")
    
    # Safely select the true top player while excluding your ID
    top = db_lb.find_one(
        {"_id": {"$ne": "1399789300387942621"}}, 
        sort=[("correct_counts", -1)]
    )
    
    # --- FIRST GAME SET LOGIC ---
    try:
        all_active_players = list(db_lb.find())
        for player in all_active_players:
            uid = player.get("_id")
            period_counts = player.get("correct_counts", 0)
            
            if period_counts > 0:
                # Overwrites/sets the score directly so it matches game 1 exactly
                db_alltime.update_one(
                    {"_id": uid},
                    {"$set": {"all_time_counts": period_counts}},
                    upsert=True
                )
        print(f"[SYSTEM] Successfully saved {len(all_active_players)} players' initial scores to All-Time.")
    except Exception as e:
        print(f"[ERROR] Failed to save all-time scores: {e}")
    # ---------------------------------
    
    if top and top.get("correct_counts", 0) > 0:
        cmd_channel = bot.get_channel(int(c3))
        if cmd_channel:
            winner_id = top.get('_id')
            msg_text = f"<@{winner_id}> has won a save slot! happy counting 🎉"
            
            # 1. Dispatch the text message straight to c3
            sent_msg = await cmd_channel.send(msg_text)
            
            # 2. Automatically pin the message to the top of the channel
            try:
                await sent_msg.pin()
                print("[SYSTEM] Successfully pinned the victory announcement message in c3.")
            except Exception as e:
                print(f"[ERROR] Failed to pin milestone message: {e}")
            
    # Reset tournament databases and update target countdown timestamp for next 14-day loop
    db_lb.delete_many({})
    db_sys.update_one(
        {"_id": "global_tournament"}, 
        {"$set": {"end_date": dt.now(tz.utc) + td(days=14)}},
        upsert=True
    )
    print("[SYSTEM] 14-day leaderboard wiped clean and extended for next round.")
