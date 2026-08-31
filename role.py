import re
from variables import *

async def check_and_update(msg, b_id):
    if not msg.embeds: return
    
    # Handle single embed element conversion cleanly
    emb = msg.embeds if isinstance(msg.embeds, list) else msg.embeds
    txt = emb.title or (emb.author.name if emb.author else "")
    name = re.sub(r"(Stats for|'s Stats|'s stats|Stats of|stats)", "", txt, flags=re.IGNORECASE).strip()
    
    # 1. FIX: Unpack the list correctly to grab the actual Member object
    res = await msg.guild.query_members(query=name, limit=1)
    if not res: return
    m = res
    
    vtxt = next((f.value for f in emb.fields if "Global Stats" in f.name), emb.description if "Global Stats" in (emb.description or "") else "")
    match = re.search(r'Score:\s*(?:\*\*)?([\d,]+)', vtxt)
    if not match: return
    
    score = int(match.group(1).replace(',', ''))
    tgt = None
    
    # Check bounds mapping loops
    for mn, mx, rname in (t if b_id == b1 else ct):
        if mn <= score <= mx: 
            tgt = rname
            break
            
    if tgt:
        r = d.utils.get(msg.guild.roles, name=tgt) or await msg.guild.create_role(name=tgt, colour=(d.Colour.purple() if b_id==b1 else d.Colour.blue()))
        
        # Override permission states down to 10k benchmarks
        val_str = tgt.replace('c', '').replace(',', '')
        if int(val_str) >= 10000:
            ch_obj = msg.guild.get_channel(int(c1 if b_id==b1 else c2))
            if ch_obj: await ch_obj.set_permissions(r, view_channel=True, send_messages=True)
            
        if r not in m.roles:
            # 2. FIX: Safely extract raw list item strings [2] instead of evaluating full tuples
            allowed_names = [k for _, _, k in (t if b_id == b1 else ct)]
            removals = [x for x in m.roles if x.name in allowed_names and x.name != tgt]
            
            if removals: 
                await m.remove_roles(*removals)
            await m.add_roles(r)
