from variables import *
from utils import ctx_parse

async def exec(tgt, user_id: str, *, custom_name: str):
    _, guild, resp = ctx_parse(tgt)
    
    cleaned_uid = user_id.replace("<", "").replace(">", "").replace("@", "").replace("!", "").replace("&", "").strip()
    clean_name = custom_name.strip()

    if not cleaned_uid.isdigit():
        return await (resp.send(" invalid User ID. Must be numbers or a profile ping.") if isinstance(tgt, c.Context) else resp.send_message(" Invalid User ID. Must be numbers or a profile ping.", ephemeral=True))

    db_cn.update_one(
        {"_id": cleaned_uid},
        {"$set": {"name": clean_name}},
        upsert=True
    )

    await (resp.send(f" Set custom name for `{cleaned_uid}` to **{clean_name}**") if isinstance(tgt, c.Context) else resp.send_message(f"✅ Set custom name for `{cleaned_uid}` to **{clean_name}**"))
