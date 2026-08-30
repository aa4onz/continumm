from variables import *
from utils import deadline

def create_paginator(v, h, c, is_lb=False, author_id=None):
    view = d.ui.View(timeout=60.0)
    view.p = 1
    view.pages = max(1, (len(v) + 9) // 10)

    def build():
        emb = d.Embed(title=h, color=c)
        if not v:
            emb.description = "Nothing here yet."
            return emb
        
        chunk = v[(view.p - 1) * 10 : view.p * 10]
        lines, m = [], ["🥇", "🥈", "🥉"]
        
        for i, item in enumerate(chunk):
            idx = ((view.p - 1) * 10) + i
            r = m[idx] if idx < 3 else f"`#{idx + 1}`"
            
            
            is_user = str(item.get('_id')) == str(author_id)
            pin_icon = " 📍" if is_user else ""
            
            if is_lb:
                lines.append(f"{r} - 💧 {item.get('correct_counts')} <@{item.get('_id')}>" + pin_icon)
            else:
                m1, m2 = item.get("mvp1_id"), item.get("mvp2_id")
                txt = f"<@{m1}>" if m1 else "None"
                if m2: txt += f" & <@{m2}>"
                lines.append(f"{r} **{round(item.get('pace', 0.0))} /hr** --- {txt}" + pin_icon)
                
        emb.description = "\n".join(lines)
        if is_lb:
            ed = deadline()["end_date"].replace(tzinfo=tz.utc) if deadline()["end_date"].tzinfo is None else deadline()["end_date"]
            emb.set_footer(text=f"Page {view.p}/{view.pages} • Rem: {max(0, (ed - dt.now(tz.utc)).days)}d")
        else:
            emb.set_footer(text=f"Page {view.p}/{view.pages}")
        return emb

    b1 = d.ui.Button(label="◀", style=d.ButtonStyle.primary, disabled=True)
    b2 = d.ui.Button(label="▶", style=d.ButtonStyle.primary, disabled=(view.pages == 1))
    b3 = d.ui.Button(emoji="📍", style=d.ButtonStyle.primary)
    b4 = d.ui.Button(emoji="🔄", style=d.ButtonStyle.primary)

    async def prev_click(it):
        if view.p > 1:
            view.p -= 1
            b1.disabled = (view.p == 1)
            b2.disabled = False
            await it.response.edit_message(embed=build(), view=view)

    async def next_click(it):
        if view.p < view.pages:
            view.p += 1
            b1.disabled = False
            b2.disabled = (view.p == view.pages)
            await it.response.edit_message(embed=build(), view=view)

    async def pin_click(it):
        
        user_idx = -1
        for idx, item in enumerate(v):
            if str(item.get('_id')) == str(it.user.id):
                user_idx = idx
                break
        
        if user_idx == -1:
            return await it.response.send_message("sorry! You aren't ranked on this leaderboard yet!", ephemeral=True)
        
        target_page = (user_idx // 10) + 1
        view.p = target_page
        
        
        b1.disabled = (view.p == 1)
        b2.disabled = (view.p == view.pages)
        await it.response.edit_message(embed=build(), view=view)

    async def reset_click(it):
        view.p = 1
        b1.disabled = True
        b2.disabled = (view.pages == 1)
        await it.response.edit_message(embed=build(), view=view)

    b1.callback = prev_click
    b2.callback = next_click
    b3.callback = pin_click
    b4.callback = reset_click
    
    view.add_item(b1)
    view.add_item(b2)
    view.add_item(b3)
    view.add_item(b4)
    view.build_embed = build
    return view
