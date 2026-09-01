import re
import discord

def parse_and_optimize(embed: discord.Embed) -> discord.Embed:
    """
    Parses the composter embed and simulates level upgrades step-by-step
    to tell the user exactly how many total coins to spend on the optimal stat.
    """
    # 1. Gather all possible text sources from the embed
    text_pieces = [
        embed.title or "",
        embed.description or ""
    ]
    for field in embed.fields:
        text_pieces.append(f"{field.name}: {field.value}")
    
    # Flatten everything into a single searchable text blob
    content_text = "\n".join(text_pieces)

    try:
        # 2. Extract Levels using text markers
        e_lvl_match = re.search(r"Efficiency\s*(?:Lvl|Level)?[:\s]*(\d+)", content_text, re.IGNORECASE)
        q_lvl_match = re.search(r"Quality\s*(?:Lvl|Level)?[:\s]*(\d+)", content_text, re.IGNORECASE)

        # 3. Extract Percentages with specific Bold Markdown handling
        # Matches: "currently **24.94%** chance" or "currently **24.94%**"
        e_current_match = re.search(r"currently\s+\*\*([\d.]+)\s*%\*\*", content_text, re.IGNORECASE)
        
        # Matches: "reduced by **13.89%**"
        q_current_match = re.search(r"reduced\s+by\s+\*\*([\d.]+)\s*%\*\*", content_text, re.IGNORECASE)

        # Validate that basic matching succeeded
        if not all([e_lvl_match, q_lvl_match, e_current_match, q_current_match]):
            raise ValueError(
                f"Parsing failed. Matches -> "
                f"E Lvl: {bool(e_lvl_match)}, Q Lvl: {bool(q_lvl_match)}, "
                f"E %: {bool(e_current_match)}, Q %: {bool(q_current_match)}"
            )

        # Assign clean numerical values
        lvl_E = int(e_lvl_match.group(1))
        lvl_Q = int(q_lvl_match.group(1))
        E = float(e_current_match.group(1)) / 100
        Q = float(q_current_match.group(1)) / 100

        # 4. Extract increment values (+0.16% and +0.2% style lines)
        e_inc_match = re.search(r"Efficiency.*?\+.*?([\d.]+)", content_text, re.DOTALL | re.IGNORECASE)
        q_inc_match = re.search(r"Quality.*?\+.*?([\d.]+)", content_text, re.DOTALL | re.IGNORECASE)
        
        e_inc = float(e_inc_match.group(1)) / 100 if e_inc_match else 0.0016
        q_inc = float(q_inc_match.group(1)) / 100 if q_inc_match else 0.0020

        # 5. Step-by-Step Level Simulation Loop
        sim_lvl_E = lvl_E
        sim_lvl_Q = lvl_Q
        sim_E = E
        sim_Q = Q
        
        simulation_steps = []
        max_simulation_steps = 40  

        for _ in range(max_simulation_steps):
            # Evaluate exact level costs using custom non-linear models
            cost_E = (sim_lvl_E ** 2) // 450 + (2 * sim_lvl_E) + 35
            cost_Q = (sim_lvl_Q ** 2) // 19 + (8 * sim_lvl_Q) + 42

            # Instantaneous profitability math
            R_E = e_inc / cost_E
            R_Q = q_inc / cost_Q
            m = (sim_Q * R_E) - (sim_E * R_Q)

            # --- DECISION ENGINE LOGIC ---
            if m > 1e-11:
                simulation_steps.append(("Efficiency", cost_E))
                sim_E += e_inc
                sim_lvl_E += 1
            elif m < -1e-11:
                simulation_steps.append(("Quality", cost_Q))
                sim_Q += q_inc
                sim_lvl_Q += 1
            else:
                if cost_E <= cost_Q:
                    simulation_steps.append(("Efficiency", cost_E))
                    sim_E += e_inc
                    sim_lvl_E += 1
                else:
                    simulation_steps.append(("Quality", cost_Q))
                    sim_Q += q_inc
                    sim_lvl_Q += 1

        # 6. Group consecutive matching targets together and sum up their coin cost
        first_target = simulation_steps[0][0] if simulation_steps else "Quality"
        total_coins_needed = 0
        levels_to_buy = 0

        for target_stat, step_cost in simulation_steps:
            if target_stat == first_target:
                total_coins_needed += step_cost
                levels_to_buy += 1
            else:
                break

        # 7. Formulate final report layout
        stat_emoji = "♻️ Efficiency" if first_target == "Efficiency" else "💎 Quality"
        color = discord.Color.green() if first_target == "Efficiency" else discord.Color.blue()
        
        report = discord.Embed(
            title="🌳 Composter Coin Investment Target",
            description=f"You should spend exactly **{total_coins_needed:,} coins** on **{stat_emoji}** next.",
            color=color
        )
        
        report.add_field(
            name="Investment Action Plan", 
            value=f"This amount will upgrade your **{first_target}** by **+{levels_to_buy} level(s)** before it's time to swap focus to the other stat.", 
            inline=False
        )
        report.add_field(
            name="Current Levels", 
            value=f"♻️ Efficiency: **Lvl {lvl_E}**\n💎 Quality: **Lvl {lvl_Q}**", 
            inline=True
        )
        
        return report

    except Exception as error:
        error_embed = discord.Embed(
            title="❌ Composter Parser Error",
            description="Failed to automatically run simulations over the provided layout bounds.",
            color=discord.Color.red()
        )
        error_embed.set_footer(text=f"Reason: {str(error)}")
        return error_embed
