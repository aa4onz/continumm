import re
import time
from variables import *
from utils import ctx_parse

def parse_msg_input(input_str: str):
    """
    Parses a message link or raw ID.
    Returns: (channel_id_int_or_None, message_id_int)
    """
    cleaned = input_str.strip()
    # Check if it's a full discord message link: https://discord.com
    link_match = re.search(r"channels/\d+/(\d+)/(\d+)\s*$", cleaned)
    if link_match:
        return int(link_match.group(1)), int(link_match.group(2))
    
    # Otherwise, assume it's a raw message ID
    id_match = re.search(r"(\d{17,20})\s*$", cleaned)
    if id_match:
        return None, int(id_match.group(1))
        
    return None, None

def extract_number(content: str) -> int:
    """Extracts the leading number from the message content."""
    match = re.match(r"^(\d+)", content.strip())
    return int(match.group(1)) if match else None

async def exec(tgt, arg1: str = None, arg2: str = None):
    chan, _, resp = ctx_parse(tgt)
    
    if not arg1 or not arg2:
        msg = "❌ Please provide two message links or IDs!\nExample: `r!cp <msg_link_1> <msg_link_2>`"
        return await (resp.send(msg) if isinstance(tgt, c.Context) else resp.send_message(msg, ephemeral=True))
    
    ch_id1, id1 = parse_msg_input(arg1)
    ch_id2, id2 = parse_msg_input(arg2)
    
    if not id1 or not id2:
        msg = "❌ Invalid message links or IDs provided."
        return await (resp.send(msg) if isinstance(tgt, c.Context) else resp.send_message(msg, ephemeral=True))
        
    try:
        # Determine the target channel for message 1
        target_chan1 = bot.get_channel(ch_id1) if ch_id1 else chan
        if not target_chan1:
            target_chan1 = await bot.fetch_channel(ch_id1)
            
        # Determine the target channel for message 2
        target_chan2 = bot.get_channel(ch_id2) if ch_id2 else chan
        if not target_chan2:
            target_chan2 = await bot.fetch_channel(ch_id2)

        # Fetch messages using their specific channel origins
        msg1 = await target_chan1.fetch_message(id1)
        msg2 = await target_chan2.fetch_message(id2)
    except Exception:
        msg = "❌ Could not find those messages. If using raw IDs, ensure they are in this exact channel. Otherwise, use full links."
        return await (resp.send(msg) if isinstance(tgt, c.Context) else resp.send_message(msg, ephemeral=True))

    # Cross-channel tracking: use the channel where the counts originated for history scans
    # Defaulting to message 1's origin channel if they happen to differ
    scan_channel = target_chan1 

    num1 = extract_number(msg1.content)
    num2 = extract_number(msg2.content)
    
    if num1 is None or num2 is None:
        msg = f"❌ One or both messages do not start with a valid number!\n• Msg 1: `{msg1.content[:20]}`\n• Msg 2: `{msg2.content[:20]}`"
        return await (resp.send(msg) if isinstance(tgt, c.Context) else resp.send_message(msg, ephemeral=True))

    # Sort messages chronologically
    first_msg, last_msg = (msg1, msg2) if msg1.created_at < msg2.created_at else (msg2, msg1)
    start_num, end_num = (num1, num2) if msg1.created_at < msg2.created_at else (num2, num1)
    
    total_counts = end_num - start_num
    
    t0 = first_msg.created_at.timestamp()
    t1 = last_msg.created_at.timestamp()
    
    duration_seconds = t1 - t0
    if duration_seconds <= 0:
        duration_seconds = 0.001
        
    hrs = duration_seconds / 3600.0
    pace = round(total_counts / hrs, 1) if total_counts > 0 else 0.0

    # Initialize set with boundary authors
    unique_players = set()
    unique_players.add(first_msg.author)
    unique_players.add(last_msg.author)

    # FAST SCAN: Only read the first 10 messages right after the start message in its source channel
    try:
        async for historical_msg in scan_channel.history(after=first_msg, limit=10):
            if historical_msg.created_at >= last_msg.created_at:
                break
            if extract_number(historical_msg.content) is not None:
                unique_players.add(historical_msg.author)
    except Exception:
        pass

    player_names = [p.name for p in unique_players]
    runners_txt = ", ".join(player_names)

    output_text = (
        f"**partial pace**\n"
        f"Start: `{start_num:,}` | End: `{end_num:,}`\n"
        f"Counts: `{total_counts:,}` in `{round(duration_seconds, 2)}`s\n"
        f"Pace: **`{pace:,} /hr`**\n"
        f"Players: {runners_txt}"
    )
    
    await (resp.send(output_text) if isinstance(tgt, c.Context) else resp.send_message(output_text))
