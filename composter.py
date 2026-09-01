import re
import discord

def parse_and_optimize(embed: discord.Embed) -> discord.Embed:
    """
    Diagnostic script to reveal exactly how the embed text looks raw.
    """
    # 1. Gather all possible text sources from the embed
    text_pieces = [
        f"TITLE: {embed.title or ''}",
        f"DESC: {embed.description or ''}"
    ]
    for i, field in enumerate(embed.fields):
        text_pieces.append(f"FIELD_{i} NAME: {field.name} | VALUE: {field.value}")
    
    # Flatten everything into a single text block
    content_text = "\n".join(text_pieces)

    # 2. Print the exact raw layout structure to your bot's terminal logs
    print("\n--- [RAW EMBED CONTENT START] ---")
    print(content_text)
    print("--- [RAW EMBED CONTENT END] ---\n")

    # 3. Return an embed showing the text structure directly in Discord
    debug_embed = discord.Embed(
        title="🔍 Embed Raw Data Structure",
        description=f"Check your bot terminal logs or read the parsed data below:",
        color=discord.Color.orange()
    )
    
    # Safely truncate text to fit Discord embed field limits (1024 chars max)
    debug_embed.add_field(
        name="Flattened Text Stream Layout", 
        value=f"```\n{content_text[:950]}\n```", 
        inline=False
    )
    return debug_embed
