import pandas as pd
import numpy as np
import math
import re
from parsel import Selector
from pathlib import Path
from functions import *

url = Path("./webpages/2025_worldchamps.html")

html = url.read_text(encoding="utf-8")
sel = Selector(text=html)


def lift(card):
    """
    Helper function called on a athlete's lifts in a certain lift. e.g. 60kg men's snatch for one athlete

    Args:
        cards: div containing data
        
    Returns:
        dictionary with data
    """
 
    info = card.css(":scope > div:first-child > div:first-child")[0]

    # Group 1: rank , name, country
    info_1 = info.css(":scope > :nth-child(1)")[0]

    strings_1 = info_1.css("p")

    rank = strings_1[0]
    rank = "".join(rank.css("::text").getall()).strip()
    rank = int(m.group(1)) if (m := re.search(r":\s*(\d+)", rank)) else np.nan

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
    birth = pd.to_datetime(birth)

    weight = strings_2[1]
    weight = "".join(weight.css("::text").getall()).strip()
    weight = re.sub("B.weight: ", "", weight)

    group = strings_2[2]
    group = "".join(group.css("::text").getall()).strip()
    group = re.sub("Group: ", "", group)

    # Group 3: Attempts and total
    info_3 = info.css(":scope > :nth-child(3)")[0]

    strings_3 = info_3.css("p")

    attempts = []
    makes = []

    # Loop through attempts. Ignore the last one for total, we'll get that info from the Total section
    for att in strings_3[:3]:

        # Get the number
        att_num = "".join(att.css("::text").getall()).strip()
        att_num = int(m.group(1)) if (m := re.search(r":\s*(\d+)", att_num)) else np.nan

        attempts.append(att_num)

        # See if there is a "strike" element, which means a missed lift
        strike = att.css("strike")

        if np.isnan(att_num):
            makes.append(pd.NA)
        elif len(strike) > 0:
            makes.append(False)
        else:
            makes.append(True)


    # Create return dict
    return {
        "Rank": rank,
        "Name": name,
        "Nation": country,
        "Born": birth,
        "Weight": weight,
        "Group": group,
        "Attempt 1": attempts[0],
        "Attempt 2": attempts[1],
        "Attempt 3": attempts[2],
        "Attempt Make 1": makes[0],
        "Attempt Make 2": makes[1],
        "Attempt Make 3": makes[2]
    }



def section(id):
    """
    Main driver function that is called on the men's or women's section of results

    Args:
        id: css id of the div that contains the relevant info

    Returns:
        df of results
    """
   
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

        # Init df
        snatch_df = pd.DataFrame(columns=SN_CJ_COLUMNS)

        for snatch in snatch_cards:
            res = lift(snatch)
            snatch_df.loc[len(snatch_df)] = res

        snatch_df["Lift"] = "Snatch"

        # Fifth div has the cj results
        cj = category[4]

        # Skip the first child div which is just the row headers
        cj_cards = cj.css(":scope > div")[1:]

        # Init df
        cj_df = pd.DataFrame(columns=SN_CJ_COLUMNS)

        for cj in cj_cards:
            res = lift(cj)
            cj_df.loc[len(cj_df)] = res

        cj_df["Lift"] = "CJ"

        # Combine and add extra info columns
        combined = pd.concat([snatch_df, cj_df])
        combined["Category"] = weight_class_num
        combined["Gender"] = gender

        # Fix int types
        for col in ["Rank", "Attempt 1", "Attempt 2", "Attempt 3"]:
            combined[col] = combined[col].astype("Int64")


        













men = section("#men_snatchjerk")
