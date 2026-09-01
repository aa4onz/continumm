import re
import discord

def parse_and_optimize(embed: discord.Embed) -> discord.Embed:
    """
    Parses the composter embed and simulates level upgrades step-by-step
    to tell the user exactly how many total coins to spend on the optimal stat.
    """
    content_text = f"{embed.title or ''}\n{embed.description or ''}"
    for field in embed.fields:
        content_text += f"\n{field.name}: {field.value}"

    try:
        # 1. Parse current feature values from the embed text layout
        e_current_match = re.search(r"([\d.]+)%\s*chance", content_text, re.IGNORECASE)
        q_current_match = re.search(r"reduced by\s*([\d.]+)%", content_text, re.IGNORECASE)

        # Parse current level positions
        e_lvl_match = re.search(r"Efficiency Lvl\s*(\d+)", content_text, re.IGNORECASE)
        q_lvl_match = re.search(r"Quality Lvl\s*(\d+)", content_text, re.IGNORECASE)

        if not all([e_current_match, q_current_match, e_lvl_match, q_lvl_match]):
            raise ValueError("Could not find all required Level, Efficiency, or Quality parameters.")

        # Establish current base status (converted to absolute decimals)
        E = float(e_current_match.group(1)) / 100
        Q = float(q_current_match.group(1)) / 100
        lvl_E = int(e_lvl_match.group(1))
        lvl_Q = int(q_lvl_match.group(1))

        # 2. Parse incremental value bounds (+0.15% -> 0.0015, +0.21% -> 0.0021)
        e_data = re.search(r"Efficiency.*?\+([\d.]+)", content_text, re.DOTALL | re.IGNORECASE)
        q_data = re.search(r"Quality.*?\+([\d.]+)", content_text, re.DOTALL | re.IGNORECASE)
        
        e_inc = float(e_data.group(1)) / 100 if e_data else 0.0015
        q_inc = float(q_data.group(1)) / 100 if q_data else 0.0021

        # 3. Step-by-Step Level Simulation Loop
        sim_lvl_E = lvl_E
        sim_lvl_Q = lvl_Q
        sim_E = E
        sim_Q = Q
        
        simulation_steps = []
        max_simulation_steps = 40  # Look ahead steps to find the streak length

        for _ in range(max_simulation_steps):
            # Calculate individual level costs using your exact custom equations
            cost_E = (sim_lvl_E ** 2) // 450 + (2 * sim_lvl_E) + 35
            cost_Q = (sim_lvl_Q ** 2) // 19 + (8 * sim_lvl_Q) + 42

            # Instantaneous profitability math
            R_E = e_inc / cost_E
            R_Q = q_inc / cost_Q
            m = (sim_Q * R_E) - (sim_E * R_Q)

            # --- DECISION ENGINE LOGIC ---
            # If Efficiency is definitively better
            if m > 1e-11:
                simulation_steps.append(("Efficiency", cost_E))
                sim_E += e_inc
                sim_lvl_E += 1
            # If Quality is definitively better    
            elif m < -1e-11:
                simulation_steps.append(("Quality", cost_Q))
                sim_Q += q_inc
                sim_lvl_Q += 1
            # If m is exactly 0 (Perfect Tie) -> Pick the cheaper option first
            else:
                if cost_E <= cost_Q:
                    simulation_steps.append(("Efficiency", cost_E))
                    sim_E += e_inc
                    sim_lvl_E += 1
                else:
                    simulation_steps.append(("Quality", cost_Q))
                    sim_Q += q_inc
                    sim_lvl_Q += 1

        # 4. Group consecutive matching targets together and sum up their coin cost
        first_target = simulation_steps[0][0]
        total_coins_needed = 0
        levels_to_buy = 0

        for target_stat, step_cost in simulation_steps:
            if target_stat == first_target:
                total_coins_needed += step_cost
                levels_to_buy += 1
            else:
                break

        # 5. Formulate final report design
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
