import re
from variables import *

async def check_and_update(msg, b_id):
    if not msg.embeds: return
    
    # Handle single embed element conversion cleanly
    emb = msg.embeds if isinstance(msg.embeds, list) else msg.embeds
    txt = emb.title or (emb.author.name if emb.author else "")
    name = re.sub(r"(Stats for|'s Stats|'s stats|Stats of|stats)", "", txt, flags=re.IGNORECASE).strip()
    
    # Extract the true Member object from the query results
    res = await msg.guild.query_members(query=name, limit=1)
    if not res: return
    m = res[0]
    
    vtxt = next((f.value for f in emb.fields if "Global Stats" in f.name), emb.description if "Global Stats" in (embed.description or "") else "")
    match = re.search(r'Score:\s*(?:\*\*)?([\d,]+)', vtxt)
    if not match: return
    
    score = int(match.group(1).replace(',', ''))
    tgt = None
    
    # Match the score against your ranking milestone brackets
    for mn, mx, rname in (t if b_id == b1 else ct):
        if mn <= score <= mx: 
            tgt = rname
            break
            
    if tgt:
        # Automatically fetch or create the role with the correct color if it does not exist
        r = d.utils.get(msg.guild.roles, name=tgt) or await msg.guild.create_role(
            name=tgt, 
            colour=(d.Colour.purple() if b_id == b1 else d.Colour.blue())
        )
        
        # Lower channel overrides permission access down to 10k benchmarks
        val_str = tgt.replace('c', '').replace(',', '')
        if int(val_str) >= 10000:
            ch_obj = msg.guild.get_channel(int(c1 if b_id == b1 else c2))
            if ch_obj: await ch_obj.set_permissions(r, view_channel=True, send_messages=True)
            
        if r not in m.roles:
            # FIX: Properly extract only the string name field from the configuration tuples
            allowed_names = [k for _, _, k in (t if b_id == b1 else ct)]
            
            # Wipe older obsolete milestone roles cleanly from their profile
            removals = [x for x in m.roles if x.name in allowed_names and x.name != tgt]
            if removals: 
                await m.remove_roles(*removals)
                
            await m.add_roles(r)
