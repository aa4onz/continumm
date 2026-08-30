from variables import *
from utils import ctx_parse

async def exec(tgt, main, alt_user):
    _, guild, resp = ctx_parse(tgt)
    row = db_lb.find_one({"_id": str(alt_user.id)})
    prev = row.get("correct_counts", 0) if row else 0
    if prev > 0:
        db_lb.update_one({"_id": str(main.id)}, {"$inc": {"correct_counts": prev}}, upsert=True)
        db_lb.delete_one({"_id": str(alt_user.id)})
    db_alt.update_one({"_id": str(alt_user.id)}, {"$set": {"main_id": str(main.id), "linked_at": dt.now(tz.utc)}}, upsert=True)
    alts[str(alt_user.id)] = str(main.id)
    r = d.utils.get(guild.roles, name="alt") or await guild.create_role(name="alt", colour=d.Colour.dark_grey())
    await alt_user.add_roles(r)
    await (resp.send(f"{alt_user.display_name} linked to {main.display_name}") if isinstance(tgt, c.Context) else resp.send_message(f"{alt_user.display_name} linked to {main.display_name}"))
  
