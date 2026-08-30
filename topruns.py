from variables import *
from utils import ctx_parse
import menus

async def exec(tgt):
    ch, _, resp = ctx_parse(tgt)
    if str(ch.id) in ch: return
    v = menus.create_paginator(list(db_top.find().sort("pace", -1).limit(100)), "Top Fastest Runs", d.Color.purple())
    await (resp.send(embed=v.build_embed(), view=v) if isinstance(tgt, c.Context) else resp.send_message(embed=v.build_embed(), view=v))
  
