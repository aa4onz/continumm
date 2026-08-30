from variables import *
from utils import ctx_parse

async def exec(tgt, main, alt_user):
    _, guild, resp = ctx_parse(tgt)
    
    # 1. Clean main if passed as a string/ping, or grab the ID if passed as a Member object
    if isinstance(main, str):
        main_id = main.replace("<@", "").replace(">", "").replace("!", "").strip()
    else:
        main_id = str(main.id)
        
    # 2. Clean alt_user if passed as a string/ping, or grab the ID if passed as a Member object
    if isinstance(alt_user, str):
        alt_id = alt_user.replace("<@", "").replace(">", "").replace("!", "").strip()
    else:
        alt_id = str(alt_user.id)

    # 3. Database operations using safe string IDs
    row = db_lb.find_one({"_id": alt_id})
    prev = row.get("correct_counts", 0) if row else 0
    
    if prev > 0:
        db_lb.update_one({"_id": main_id}, {"$inc": {"correct_counts": prev}}, upsert=True)
        db_lb.delete_one({"_id": alt_id})
        
    db_alt.update_one({"_id": alt_id}, {"$set": {"main_id": main_id, "linked_at": dt.now(tz.utc)}}, upsert=True)
    alts[alt_id] = main_id
    
    # 4. Safely attempt to apply the server role 
    try:
        member_obj = guild.get_member(int(alt_id)) or await guild.fetch_member(int(alt_id))
        if member_obj:
            r = d.utils.get(guild.roles, name="alt") or await guild.create_role(name="alt", colour=d.Colour.dark_grey())
            await member_obj.add_roles(r)
    except:
        pass

    # 5. Fetch display names for a clean output look
    m_user = bot.get_user(int(main_id))
    m_name = m_user.display_name if m_user else f"User-{main_id}"
    
    a_user = bot.get_user(int(alt_id))
    a_name = a_user.display_name if a_user else f"User-{alt_id}"
    
    await (resp.send(f"{a_name} linked to {m_name}") if isinstance(tgt, c.Context) else resp.send_message(f"{a_name} linked to {m_name}"))
