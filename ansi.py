CLR = "\u001b[0m"
ESC = "\u001b["

RED = "0;31m"
ORG = "0;33m"
PRP = "0;35m"
BLU = "0;34m"
CYN = "0;36m"
GRN = "0;32m"
GRY = "0;30m"

def paint(text, color_code):
    return f"{ESC}{color_code}{text}{CLR}"

def run_color(rank):
    if rank <= 2: return RED
    if rank == 3: return ORG
    if 4 <= rank <= 10: return PRP
    if 11 <= rank <= 20: return BLU
    if 21 <= rank <= 30: return CYN
    if 31 <= rank <= 50: return GRN
    return GRY
