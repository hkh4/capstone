import pandas
import math
import re
from parsel import Selector
from pathlib import Path
from functions import *

url = Path("./webpages/2025_worldchamps.html")

html = url.read_text(encoding="utf-8")
sel = Selector(text=html)

SNATCH_CJ_ROWS = ["Rank", "Name", "Nation", "Born", "Weight", "Group", "Att1", "Att2", "Att3", "Total"]
TOTAL_ROWS = ["Rank", "Name", "Nation", "Born", "Weight", "Group", "Snatch", "CJ", "Total"]

def section(id):
   
    container = sel.css(id)

    # Grab all divs
    divs = container.css(":scope > div")

    # Raise an error is there isn't a mulitple of 7 divs
    if len(divs) % 7 != 0:
        raise ValueError(
            f"Expected multiple of 7 divs, got {len(divs)}"
        )
    
    # Groups of 7 divs should follow the format:
    # 1. Name of weight class category
    # 2. Snatch
    # 3. Snatch results
    # 4. C&J
    # 5. C&J results
    # 6. Total
    # 7. Total results

    for i in range(math.floor(len(divs) / 7)):

        # Grab group of 7
        category = divs[i*7:i*7 + 7]

        # First div has the weight category and gender
        weight_class = category[0].css("h3::text").get()
        weight_class_num = re.search(r"\d+", weight_class).group()
        gender = re.search(r"[A-Za-z]+$", weight_class).group()

        # Third div has the snatch results
        snatches = category[2]

        # Skip the first child div which is just the row headers
        snatch_cards = snatches.css(":scope > div")[1:]

        # Track rank, easier than pulling
        rank = 1

        for snatch in snatch_cards:
            
            info = snatch.css(":scope > div:first-child > div:first-child")[0]

            # Group 1: rank (ignored), name, country
            info_1 = info.css(":scope > :nth-child(1)")[0]

            strings_1 = info_1.css("p")

            name = strings_1[1]
            name = "".join(name.css("::text").getall()).strip()

            country = strings_1[2]
            country = "".join(country.css("::text").getall()).strip()

            # Group 2: birthdate, weight, group
            info_2 = info.css(":scope > :nth-child(2)")[0]

            strings_2 = info_2.css("p")

            birth = strings_2[0]
            birth = "".join(birth.css("::text").getall()).strip()
            birth = re.sub("Born: ", "", birth)

            weight = strings_2[1]
            weight = "".join(weight.css("::text").getall()).strip()
            weight = re.sub("B.weight: ", "", weight)

            group = strings_2[2]
            group = "".join(group.css("::text").getall()).strip()
            group = re.sub("Group: ", "", group)

            # Group 3: Attempts and total
            info_3 = info.css(":scope > :nth-child(3)")[0]

            rank += 1













men = section("#men_snatchjerk")
