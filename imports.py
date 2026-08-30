import os, re, time, asyncio, certifi
import discord as d
from discord.ext import commands as c
from discord import app_commands as ac
from pymongo import MongoClient as mc
from apscheduler.schedulers.asyncio import AsyncIOScheduler as s
from datetime import datetime as dt, timedelta as td, timezone as tz
