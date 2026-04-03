from parse import *
from parsel import Selector 
from pathlib import Path
import pandas as pd


master_lifts = []
master_totals = []


# Get all files of interest
for fp in Path("webpages").glob("*.html"):

   print(f"Working on {fp}...")
   
   # filename
   filename = fp.stem

   # read in the file
   html = fp.read_text(encoding="utf-8")
   sel = Selector(text=html)

   men_lifts, men_total = section(sel, "#men_snatchjerk")
   women_lifts, women_total = section(sel, "#women_snatchjerk")

   # Combine into single df
   lifts = pd.concat([men_lifts, women_lifts])
   totals = pd.concat([men_total, women_total])

   # Add in event info
   lifts["Event"] = filename
   totals["Event"] = filename

   master_lifts.append(lifts)
   master_totals.append(totals)



master_lifts_combined = pd.concat(master_lifts)
master_totals_combined = pd.concat(master_totals)

master_lifts_combined.drop_duplicates(inplace=True)
master_totals_combined.drop_duplicates(inplace=True)


# ---------------------------------- Errors ---------------------------------- #
# There are two lifters that have errors on the IWF official website. These are the ones I caught
mask1 = (
   (master_lifts_combined["Name"] == "ADAMUS Bartlomiej Stefan") &
   (master_lifts_combined["Gender"] == "Women")
)
master_lifts_combined.loc[mask1, ["Name", "Nation", "Born"]] = [
   "ARDALSBAKKE Marit",
   "NOR",
   pd.to_datetime("1992-05-11 00:00:00")
]

mask2 = (
   (master_lifts_combined["Name"] == "ALAMEER Hanan Y M A H") & 
   (master_lifts_combined["Category"] == "64")
)

master_lifts_combined.loc[mask2, ["Name", "Nation", "Born"]] = [
   "FATEMEH Majid Naroei",
   "UAE",
   pd.to_datetime("2001-09-06")
]

# Same thing for the totals
mask1 = (
   (master_totals_combined["Name"] == "ADAMUS Bartlomiej Stefan") &
   (master_totals_combined["Gender"] == "Women")
)
master_totals_combined.loc[mask1, ["Name", "Born"]] = [
   "ARDALSBAKKE Marit",
   pd.to_datetime("1992-05-11 00:00:00")
]

mask2 = (
   (master_totals_combined["Name"] == "ALAMEER Hanan Y M A H") & 
   (master_totals_combined["Category"] == "64")
)

master_totals_combined.loc[mask2, ["Name", "Born"]] = [
   "FATEMEH Majid Naroei",
   pd.to_datetime("2001-09-06")
]




# DQs
dq1 = (
   (master_lifts_combined["Name"] == "ALEMAN ARDON Sofia Isabel") & 
   (master_lifts_combined["Born"] == pd.to_datetime("2001-09-10 00:00:00")) & 
   (master_lifts_combined["Event"] == "2023_panamgames")
)

dq2 = (
   (master_lifts_combined["Name"] == "VACHON Nicolas") & 
   (master_lifts_combined["Born"] == pd.to_datetime("1996-07-05 00:00:00")) & 
   (master_lifts_combined["Event"] == "2023_panamgames")
)

master_lifts_combined = master_lifts_combined[(~dq1) & (~dq2)].copy()

dq1_t = (
   (master_totals_combined["Name"] == "ALEMAN ARDON Sofia Isabel") & 
   (master_totals_combined["Born"] == pd.to_datetime("2001-09-10 00:00:00")) & 
   (master_totals_combined["Event"] == "2023_panamgames")
)

dq2_t = (
   (master_totals_combined["Name"] == "VACHON Nicolas") & 
   (master_totals_combined["Born"] == pd.to_datetime("1996-07-05 00:00:00")) & 
   (master_totals_combined["Event"] == "2023_panamgames")
)

master_totals_combined = master_totals_combined[(~dq1_t) & (~dq2_t)].copy()




# Missing data
missing1 = (
   (master_lifts_combined["Name"] == "QUINTANA MENDOZA Rosielis Coromoto") & 
   (master_lifts_combined["Born"] == pd.to_datetime("2000-03-18 00:00:00")) & 
   (master_lifts_combined["Event"] == "2023_grandprix1")
)

missing2 = (
   (master_lifts_combined["Name"] == "CASTILLO CONTRERAS Thalia Fidelia") & 
   (master_lifts_combined["Born"] == pd.to_datetime("2005-11-28 00:00:00")) & 
   (master_lifts_combined["Event"] == "2023_grandprix1")
)

master_lifts_combined = master_lifts_combined[(~missing1) & (~missing2)].copy()

missing1_t = (
   (master_totals_combined["Name"] == "QUINTANA MENDOZA Rosielis Coromoto") & 
   (master_totals_combined["Born"] == pd.to_datetime("2000-03-18 00:00:00")) & 
   (master_totals_combined["Event"] == "2023_grandprix1")
)

missing2_t = (
   (master_totals_combined["Name"] == "CASTILLO CONTRERAS Thalia Fidelia") & 
   (master_totals_combined["Born"] == pd.to_datetime("2005-11-28 00:00:00")) & 
   (master_totals_combined["Event"] == "2023_grandprix1")
)

master_totals_combined = master_totals_combined[(~missing1_t) & (~missing2_t)].copy()

master_totals_combined["Born"] = pd.to_datetime(master_totals_combined["Born"])




# ---------------------------- Create wide version --------------------------- #

# to pivot columns
to_pivot = ["Rank", "Attempt 1", "Attempt 2", "Attempt 3", "Attempt Make 1", "Attempt Make 2", "Attempt Make 3"]

# key columns
key_columns = list(master_lifts_combined.columns)
key_columns = [k for k in key_columns if not k in to_pivot]
key_columns.remove("Lift")

lifts_pivot = master_lifts_combined.pivot(index=key_columns, columns="Lift", values=to_pivot).reset_index()
lifts_pivot.columns = [f"{b} {a}".strip() for a, b in lifts_pivot.columns]

# Bring in total amounts
final_wide = pd.merge(lifts_pivot, master_totals_combined, how="left").reset_index(drop=True)

final_wide = final_wide.sort_values(by=["Event", "Gender", "Category", "Rank"]).reset_index(drop=True)

# Bring in dates
final_wide["Date"] = final_wide["Event"].map(DATES)
final_wide["Date"] = pd.to_datetime(final_wide["Date"])

# Fix NA values
final_wide["Snatch Attempt Make 1"] = final_wide["Snatch Attempt Make 1"].astype("boolean")
final_wide["Snatch Attempt Make 2"] = final_wide["Snatch Attempt Make 2"].astype("boolean")
final_wide["Snatch Attempt Make 3"] = final_wide["Snatch Attempt Make 3"].astype("boolean")
final_wide["CJ Attempt Make 1"] = final_wide["CJ Attempt Make 1"].astype("boolean")
final_wide["CJ Attempt Make 2"] = final_wide["CJ Attempt Make 2"].astype("boolean")
final_wide["CJ Attempt Make 3"] = final_wide["CJ Attempt Make 3"].astype("boolean")

for col in ["Rank", "Snatch Best", "CJ Best", "Total", "CJ Rank", "Snatch Rank", "Snatch Attempt 1", "Snatch Attempt 2", "Snatch Attempt 3", "CJ Attempt 1", "CJ Attempt 2", "CJ Attempt 3"]:
            final_wide[col] = final_wide[col].astype("Int64")

final_wide.to_pickle("./data/data.pkl")
