from variables import *

def ctx_parse(tgt):
    return (tgt.channel, tgt.guild, tgt) if isinstance(tgt, c.Context) else (tgt.channel, tgt.guild, tgt.response)

def deadline():
    r = db_sys.find_one({"_id": "global_tournament"})
    if not r:
        r = {"_id": "global_tournament", "end_date": dt.now(tz.utc) + td(days=14)}
        db_sys.insert_one(r)
    return r

def get_main(uid):
    uid_str = str(uid)
    # Check fast cache first
    if uid_str in alts:
        return alts[uid_str]
    # Direct database lookup safety net fallback
    doc = db_alt.find_one({"_id": uid_str})
    if doc:
        main_id = str(doc.get("main_id"))
        alts[uid_str] = main_id  # Save to memory cache for next count speed
        return main_id
    return uid_str

def score_up(uid):
    db_lb.update_one({"_id": get_main(uid)}, {"$inc": {"correct_counts": 1}}, upsert=True)

def race_up(cid, uid):
    db_rc.update_one({"_id": f"race_{cid}"}, {"$inc": {f"players.{get_main(uid)}": 1, "total_counts": 1}})
