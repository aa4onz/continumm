import re
import traceback
from variables import *

async def check_and_update(msg, b_id):
    try:
        print(f"[DEBUG] check_and_update triggered by bot ID: {b_id}")
        if not msg.embeds: 
            print("[DEBUG] Exiting: No embeds found in message.")
            return
            
        emb = msg.embeds[0] if isinstance(msg.embeds, list) else msg.embeds
        txt = emb.title or (emb.author.name if emb.author else "")
        print(f"[DEBUG] Found embed content text header: '{txt}'")
        
        if not txt:
            print("[DEBUG] Exiting: Header text is empty.")
            return

        name = re.sub(r"(Stats for|'s Stats|'s stats|Stats of|stats)", "", txt, flags=re.IGNORECASE).strip()
        print(f"[DEBUG] Cleaned username parsed from embed: '{name}'")
        
        # 1. Look up the member
        res = await msg.guild.query_members(query=name, limit=1)
        if not res: 
            print(f"[DEBUG] Exiting: Could not find user '{name}' in server member query search.")
            return
        m = res[0]
        print(f"[DEBUG] Successfully located server member object: {m.display_name} (ID: {m.id})")
        
        # 2. Extract stats text block
        vtxt = next((f.value for f in emb.fields if "Global Stats" in f.name), emb.description if "Global Stats" in (emb.description or "") else "")
        print(f"[DEBUG] Extracted Global Stats text section: {vtxt}")
        
        if not vtxt:
            print("[DEBUG] Exiting: Global Stats text field block not found.")
            return

        # 3. Parse the score
        match = re.search(r'Score:\s*(?:\*\*)?([\d,]+)', vtxt)
        if not match: 
            print("[DEBUG] Exiting: Regex could not locate 'Score:' pattern inside stats text.")
            return
            
        score = int(match.group(1).replace(',', ''))
        print(f"[DEBUG] Parsed final score integer: {score}")
        
        # 4. Evaluate role target
        tgt = None
        for mn, mx, rname in (t if b_id == b1 else ct):
            if mn <= score <= mx: 
                tgt = rname
                break
        print(f"[DEBUG] Matching milestone role target discovered: '{tgt}'")
                
        if tgt:
            # Fetch or create the role blueprint
            r = discord.utils.get(msg.guild.roles, name=tgt)
            if not r:
                print(f"[DEBUG] Role '{tgt}' does not exist. Attempting to create it...")
                r = await msg.guild.create_role(name=tgt, colour=(discord.Colour.purple() if b_id == b1 else discord.Colour.blue()))
                print(f"[DEBUG] Successfully created role: '{tgt}'")
            
            # Update permissions down to 10k benchmarks
            val_str = tgt.replace('c', '').replace(',', '')
            if int(val_str) >= 10000:
                ch_obj = msg.guild.get_channel(int(c1 if b_id == b1 else c2))
                if ch_obj: 
                    await ch_obj.set_permissions(r, view_channel=True, send_messages=True)
                    print(f"[DEBUG] Updated channel access overrides for role '{tgt}'")
                
            # 5. Check and update roles
            if r not in m.roles:
                print(f"[DEBUG] User doesn't have the role '{tgt}'. Starting rank sync processing...")
                allowed_names = [k for _, _, k in (t if b_id == b1 else ct)]
                removals = [x for x in m.roles if x.name in allowed_names and x.name != tgt]
                
                if removals: 
                    print(f"[DEBUG] Removing {len(removals)} old milestone roles from user...")
                    await m.remove_roles(*removals)
                    
                await m.add_roles(r)
                print(f"[DEBUG] SUCCESS: Assigned role '{tgt}' to user {m.display_name}!")
            else:
                print(f"[DEBUG] User already has the role '{tgt}'. No assignment adjustments required.")

    except Exception as e:
        print("[CRITICAL ERROR] Error running check_and_update function pipeline:")
        traceback.print_exc()
