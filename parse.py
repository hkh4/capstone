import pandas as pd
import numpy as np
import math
import re
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from functions import *


def parse_lift(card):
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
    rank = int(m.group(1)) if (m := re.search(r":\s*(\d+)", rank)) else pd.NA

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
        att_num = int(m.group(1)) if (m := re.search(r":\s*(\d+)", att_num)) else pd.NA

        attempts.append(att_num)

        # See if there is a "strike" element, which means a missed lift
        strike = att.css("strike")

        if pd.isna(att_num):
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



def parse_total(card):

    """
    Helper function to retrieve total info
    snatch best, cj best, overall rank, total
    Note: doesn't grab all columns, since not all are necessary

    Args:
        cards: div containing data
        
    Returns:
        dictionary with data
    """
    info = card.css(":scope > div:first-child > div:first-child")[0]

    # Group 1: rank and name. Don't need country
    info_1 = info.css(":scope > :nth-child(1)")[0]

    strings_1 = info_1.css("p")

    rank = strings_1[0]
    rank = "".join(rank.css("::text").getall()).strip()
    rank = int(m.group(1)) if (m := re.search(r":\s*(\d+)", rank)) else pd.NA

    name = strings_1[1]
    name = "".join(name.css("::text").getall()).strip()

    # Group 2: birthdate
    info_2 = info.css(":scope > :nth-child(2)")[0]

    strings_2 = info_2.css("p")

    birth = strings_2[0]
    birth = "".join(birth.css("::text").getall()).strip()
    birth = re.sub("Born: ", "", birth)
    birth = pd.to_datetime(birth)

    # Group 3: Bests and total
    info_3 = info.css(":scope > :nth-child(3)")[0]

    strings_3 = info_3.css("p")

    snatch_best = "".join(strings_3[0].css("::text").getall()).strip()
    snatch_best = int(m.group(0)) if (m := re.search(r"\d+", snatch_best)) else pd.NA

    cj_best = "".join(strings_3[1].css("::text").getall()).strip()
    cj_best = int(m.group(0)) if (m := re.search(r"\d+", cj_best)) else pd.NA

    total_best = "".join(strings_3[2].css("::text").getall()).strip()
    total_best = int(m.group(0)) if (m := re.search(r"\d+", total_best)) else pd.NA


    return {
        "Rank": rank,
        "Name": name,
        "Born": birth,
        "Snatch Best": snatch_best,
        "CJ Best": cj_best,
        "Total": total_best
    }







def section(sel, id):
    """
    Main driver function that is called on the men's or women's section of results

    Args:
        sel: Selector object containing entire HTML page
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


    # Initialize final dataframes
    combined_final_df = pd.DataFrame(columns=SN_CJ_COLUMNS)
    total_final_df = pd.DataFrame(columns=TOTAL_COLUMNS)
    
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
        weight_class = weight_class.strip()
        weight_class_num = re.search(r"^[^ ]+", weight_class).group(0)
        gender = re.search(r"[A-Za-z]+$", weight_class).group()

        # Third div has the snatch results
        snatches = category[2]

        # Skip the first child div which is just the row headers
        snatch_cards = snatches.css(":scope > div")[1:]

        # Init df
        snatch_df = pd.DataFrame(columns=SN_CJ_COLUMNS)

        for snatch in snatch_cards:
            res = parse_lift(snatch)
            snatch_df.loc[len(snatch_df)] = res

        snatch_df["Lift"] = "Snatch"

        # Fifth div has the cj results
        cj = category[4]

        # Skip the first child div which is just the row headers
        cj_cards = cj.css(":scope > div")[1:]

        # Init df
        cj_df = pd.DataFrame(columns=SN_CJ_COLUMNS)

        for cj in cj_cards:
            res = parse_lift(cj)
            cj_df.loc[len(cj_df)] = res

        cj_df["Lift"] = "CJ"

        # Combine and add extra info columns
        combined = pd.concat([snatch_df, cj_df])
        combined["Category"] = weight_class_num
        combined["Gender"] = gender

        # Fix int types
        for col in ["Rank", "Attempt 1", "Attempt 2", "Attempt 3"]:
            combined[col] = combined[col].astype("Int64")


        # 7th div is the total
        total = category[6]

        total_cards = total.css(":scope > div")[1:]
        total_df = pd.DataFrame(columns=TOTAL_COLUMNS)

        for t in total_cards:
            res = parse_total(t)
            total_df.loc[len(total_df)] = res


        # Add extra info columns
        total_df["Category"] = weight_class_num
        total_df["Gender"] = gender

        # Concat to the final dfs
        combined_final_df = pd.concat([combined_final_df, combined])
        total_final_df = pd.concat([total_final_df, total_df])

    return combined_final_df, total_final_df

        





