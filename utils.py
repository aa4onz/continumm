from variables import *

def ctx_parse(tgt):
    return (tgt.channel, tgt.guild, tgt) if isinstance(tgt, c.Context) else (tgt.channel, tgt.guild, tgt.response)

def deadline():
    r = db_sys.find_one({"_id": "global_tournament"})
    if not r:
        r = {"_id": "global_tournament", "end_date": dt.now(tz.utc) + td(days=14)}
        db_sys.insert_one(r)
    return r

def score_up(uid):
    db_lb.update_one({"_id": alts.get(str(uid), str(uid))}, {"$inc": {"correct_counts": 1}}, upsert=True)

def race_up(cid, uid):
    db_rc.update_one({"_id": f"race_{cid}"}, {"$inc": {f"players.{alts.get(str(uid), str(uid))}": 1, "total_counts": 1
                                                      }})
