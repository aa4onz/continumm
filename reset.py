from variables import *
from utils import ctx_parse

async def exec(tgt):
    _, _, resp = ctx_parse(tgt)
    db_lb.delete_many({})
    db_sys.update_one({"_id": "global_tournament"}, {"$set": {"end_date": dt.now(tz.utc) + td(days=14)}}, upsert=True)
    await (resp.send("**game reset!**") if isinstance(tgt, c.Context) else resp.send_message("**game reset!**"))
  
