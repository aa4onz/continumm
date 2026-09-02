from imports import *

px = ["r!", "R!", "m!", "M!", "w!", "W!"]
intents = d.Intents.default()
intents.message_content, intents.members = True, True
bot = c.Bot(command_prefix=px, intents=intents)
cron = s()

tok = os.getenv('DISCORD_TOKEN')
uri = os.getenv('MONGO_URI')

b1 = 510016054391734273    
b2 = 639599059036012605    

c1 = str(os.getenv('c1')).strip()  
c2 = str(os.getenv('c2')).strip()  
c3 = str(os.getenv('c3')).strip()  
ch = [c1, c2]

cache = {c1: {"n": None, "u": None}, c2: {"n": None, "u": None}}
alts = {}

conn = mc(uri, tlsCAFile=certifi.where())
db = conn["counting_bot_db"]
db_lb  = db["leaderboard"]
db_sys = db["system_state"]
db_rc  = db["active_races"]
db_top = db["top_races"]
db_alt = db["account_links"]
db_alltime = db["alltime_leaderboard"] 
db_cn = db["custom_names"] 


t = [
    (3000000, 3999999, "3,000,000"), (2000000, 2999999, "2,000,000"),
    (1000000, 1999999, "1,000,000"), (750000,  999999,  "750,000"),
    (500000,  749999,  "500,000"),  (250000,  499999,  "250,000"),
    (100000,  249999,  "100,000"),  (75000,   99999,   "75,000"),
    (50000,   74999,   "50,000"),   (25000,   49999,   "25,000"),
    (10000,   24999,   "10,000"),   (5000,    9999,    "5,000")
]
ct = [(mn, mx, f"{n}c") for mn, mx, n in t]

