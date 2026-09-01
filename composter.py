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

        # 3. Extract Percentages handling Markdown Bold Formatting (**XX.XX%**)
        # This matches any standalone percentage value inside asterisks anywhere in the embed text
        bold_percentages = re.findall(r"\*\*([\d.]+)\s*%\*\*", content_text)

        # Validate that fundamental parsing checks succeeded
        if not e_lvl_match or not q_lvl_match or len(bold_percentages) < 2:
            raise ValueError(
                f"Parsing failed. Found -> "
                f"E Lvl: {bool(e_lvl_match)}, Q Lvl: {bool(q_lvl_match)}, "
                f"Bold Percentages Found: {len(bold_percentages)}"
            )

        # Assign positions based on the established sequential layout structure
        lvl_E = int(e_lvl_match.group(1))
        lvl_Q = int(q_lvl_match.group(1))
        
        # The first bold percentage is Efficiency, the second is Quality
        E = float(bold_percentages[0]) / 100
        Q = float(bold_percentages[1]) / 100

        # 4. Extract upgrade increments (+0.16% and +0.2% values)
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
            # Evaluate individual upgrade level costs using custom non-linear models
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

        # 7. Formulate final report design layout card
        stat_emoji = "♻️ Efficiency" if first_target == "Efficiency" else "💎 Quality"
        color = discord.Color.green() if first_target == "Efficiency" else discord.Color.blue()
        
        report = discord.Embed(
            title="🌳WHERE U SHOULD SPEND TREE COINS",
            description=f"u should spend **{total_coins_needed:,} coins** on **{stat_emoji}** next.",
            color=color
        )
        lv = "level"
        if levels_to_buy >1:
            lv = "levels"
        report.add_field(
            name="INVESTMENT PLAN", 
            value=f"this amount will upgrade your **{first_target}** by **{levels_to_buy} {lv}** before it's time to swap.", 
            inline=False
        )
        report.add_field(
            name="current level", 
            value=f"♻️ Efficiency: ** {lvl_E}**\n💎 Quality: **{lvl_Q}**", 
            inline=True
        )
        
        return report

    except Exception as error:
        error_embed = discord.Embed(
            title="Composter Parser Error",
            description="Failed to automatically run simulations over the provided layout bounds.",
            color=discord.Color.red()
        )
        error_embed.set_footer(text=f"Reason: {str(error)}")
        return error_embed
