import asyncio
from variables import *

async def auto_run_migration():
    # Wait 5 seconds after boot to ensure database connections are fully ready
    await asyncio.sleep(5)
    print("[MIGRATION] Starting automatic database migration loop...")
    
    try:
        # 1. Read current live 14-day scores
        active_scores = list(db_lb.find())
        if not active_scores:
            print("[MIGRATION] Skipped: No active players found in the 14-day data.")
            return
            
        migrated_count = 0
        for player in active_scores:
            uid = player.get("_id")
            current_counts = player.get("correct_counts", 0)
            
            if current_counts > 0:
                # 2. Seed the values directly into your persistent all-time collection
                db_alltime.update_one(
                    {"_id": uid},
                    {"$set": {"all_time_counts": current_counts}},
                    upsert=True
                )
                migrated_count += 1
                
        print(f"[MIGRATION] SUCCESS! Seeded {migrated_count} players into the All-Time leaderboard collection!")
        
    except Exception as e:
        print(f"[MIGRATION ERROR] Critical failure: {e}")

# --- AUTOMATIC BOOT EXECUTION LAYER ---
# This forces the script to run itself the millisecond your container starts up!
asyncio.create_task(auto_run_migration())
