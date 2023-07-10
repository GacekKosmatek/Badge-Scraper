from database import SessionLocal, engine
from models import Badge, Base
from datetime import datetime
# import traceback
import asyncio
import aiohttp
import discord
import json
import time

STARTER = 14417332
try:
    with open("last_badge", "r") as f:
        STARTER = int(f.read().strip()) # type: ignore -- yap idc about ur silly constant
except Exception: pass

FREE_BADGE_UPDATE = 1645682400
DEFAULT_PARAMS = { "limit": 100, "sortOrder": "Asc" }
database = SessionLocal()
Base.metadata.create_all(bind=engine)

currentYear = None

with open("config.json", "r") as f:
    config = json.load(f)
    THREAD_LIMIT = config["threadLimit"]
    BATCH_SIZE = config["batchSize"]
    WEBHOOK = config["webhook"]

def convert_seconds(seconds: int):
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    time_string = ""
    if hours > 0:
        time_string += f"{hours}h "
    if minutes > 0:
        time_string += f"{minutes}m "
    if remaining_seconds > 0 or time_string == "":
        time_string += f"{remaining_seconds}s"
    
    return time_string.strip()

async def main():
    i = 0
    semaphore = asyncio.Semaphore(THREAD_LIMIT)
    message = None
    
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK, session=session)
        start_time = 0
        while True:
            try:
                start_time = int(time.perf_counter())
                start = i * BATCH_SIZE + STARTER
                end = (i + 1) * BATCH_SIZE + STARTER

                tasks = [
                    asyncio.create_task(
                        checkBadge(semaphore, session, i)
                    ) for i in range(start, end, 1)
                ]
                await asyncio.gather(*tasks)

                embed = discord.Embed(title="Badge Scraper", description=f"**Current Year** - {currentYear}" if currentYear else None, timestamp=datetime.now(), color=0x2B2D31)
                embed.add_field(name="Badges Found", value=len(database.query(Badge).all()), inline=True)
                embed.add_field(name="Paid Badges Found", value=len(database.query(Badge).filter(Badge.paid == True).all()), inline=True)
                embed.add_field(name="Legacy Badges Found", value=len(database.query(Badge).filter(Badge.legacy == True).all()), inline=True)
                embed.add_field(name="From", value=STARTER, inline=True)
                embed.add_field(name="To", value=end, inline=True)
                embed.add_field(name="Badges Checked", value=end - STARTER, inline=True)
                embed.set_footer(text=f"{BATCH_SIZE / 1000}k badges scraped in {convert_seconds(int(time.perf_counter()) - start_time)}", icon_url="https://media.discordapp.net/stickers/863848295629324299.webp")
                if not message:
                    message = (await webhook.send(embed=embed, wait=True)).id
                else:
                    await webhook.edit_message(message, embed=embed)

                with open("last_badge", "w") as f:
                    f.write(str(end + 1))
                i += 1
            except (KeyboardInterrupt, SystemExit): break
            else: database.commit()

async def checkBadge(semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, id: int):
    global currentYear
    async with semaphore:
        while True:
            try:
                async with session.get(f"https://badges.roblox.com/v1/badges/{id}") as r:
                    if (r.status == 200):
                        resp = await r.json()
                        created_at = datetime.fromisoformat(resp["created"])
                        if ((currentYear or 0) < created_at.year): currentYear = created_at.year
                        legacy = False
                        paid = False
                        if created_at.timestamp() < FREE_BADGE_UPDATE:
                            legacy = True
                            paid = True
                        else:
                            universe = resp['awardingUniverse']['id']
                            params = DEFAULT_PARAMS.copy()
                            badges_today = [] # today as in the day we are checking
                            today = None # Same here
                            while True:
                                async with session.get(f"https://badges.roblox.com/v1/universes/{universe}/badges", params=params) as r:
                                    resp = await r.json()
                                    
                                    for badge in resp["data"]:
                                        created = badge["created"].split("T")[0]
                                        if today != created:
                                            today = created
                                            badges_today = []
                                        
                                        if badge["id"] == id:
                                            paid = len(badges_today) > 5 # 5 free badges a day 🤯
                                            if paid:
                                                print("paid")
                                            break
                                    
                                    if cursor := resp["nextPageCursor"]: # basically if resp["nextPageCursor"] but assigns it to the var cursor
                                        params["cursor"] = cursor
                                    else:
                                        break
                                    

                        database.add(Badge(id=id, legacy=legacy, paid=paid))
                    elif (r.status not in (404, 500)):
                        print(f"[*] [{id}] Status Code {r.status}")
            except Exception: pass #traceback.print_exc()
            else: break

if __name__ == "__main__":
    asyncio.run(main())
