import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree import plot_tree
from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt

data = pd.read_pickle("./data/data.pkl")

# ---------------------------------------------------------------------------- #
#                            Section 1: Basic Stats                            #
# ---------------------------------------------------------------------------- #

# ------------------------------- Lifter stats ------------------------------- #

# Age and gender
data["Age"] = (data["Date"] - data["Born"]).dt.days / 365.25
data["age_years"] = np.floor(data["Age"])
age_gender = data.groupby(["Gender", "age_years"]).size().reset_index()


# ---------------------- Make/miss % by lift and attempt --------------------- #

make_miss = data[
   ["Snatch Attempt Make 1", "Snatch Attempt Make 2", "Snatch Attempt Make 3",
    "CJ Attempt Make 1", "CJ Attempt Make 2", "CJ Attempt Make 3"]
].agg("mean")

make_miss_gender = data.groupby("Gender").agg(
   snatch_1 = ("Snatch Attempt Make 1", "mean"),
   snatch_2 = ("Snatch Attempt Make 2", "mean"),
   snatch_3 = ("Snatch Attempt Make 3", "mean"),
   cj_1 = ("CJ Attempt Make 1", "mean"),
   cj_2 = ("CJ Attempt Make 2", "mean"),
   cj_3 = ("CJ Attempt Make 3", "mean")
).reset_index()



# ---------------------------- Stats after a miss ---------------------------- #

# After a miss on snatch 1, snatch 2, cj 1, or cj 2, how often does the lifter retake and how often do they go up
def reattempt_stats(lift, n):

   l0 = f"{lift} Attempt {str(n-1)}"
   l1 = f"{lift} Attempt {str(n)}"
   l2 = f"{lift} Attempt {str(n+1)}"
   a0 = f"{lift} Attempt Make {str(n-1)}"
   a1 = f"{lift} Attempt Make {str(n)}"
   a2 = f"{lift} Attempt Make {str(n+1)}"

   # Get only rows where the attempt missed
   sub = data[~data[a1]].copy()
   # Make sure the next row isn't NA
   sub = sub[~pd.isna(sub[a2])].copy()

   # Look at what percent were retaken vs went up
   sub["retaken"] = sub[l1] == sub[l2]
   percent_retaken = sub.agg(
      percent_retaken = ("retaken", "mean")
   ).reset_index()

   # What was the make percentage for retaking vs going up
   make_percent = sub.groupby("retaken").agg(
      make = (a2, "mean")
   ).reset_index()

   # For second attempt misses, what happened first attempt and how does that relate to bumping up?
   if n>1:
      percent_retaken_first = sub.groupby(a0).agg(
         percent_retaken = ("retaken", "mean")
      ).reset_index()


   # Format final return
   return pd.Series({
      "n": len(sub),
      "Lift": f"{lift} {str(n)}",
      "Percent Retaken": percent_retaken["retaken"].iloc[0],
      "Percent Retaken If First Make": pd.NA if n == 1 else percent_retaken_first["percent_retaken"].iloc[1],
      "Percent Retaken If First Miss": pd.NA if n == 1 else percent_retaken_first["percent_retaken"].iloc[0],
      "Retaken Make %": make_percent["make"].iloc[1],
      "Bump Up Make %": make_percent["make"].iloc[0],
   })


snatch_1_reattempt = reattempt_stats("Snatch", 1)
snatch_2_reattempt = reattempt_stats("Snatch", 2)
cj_1_reattempt = reattempt_stats("CJ", 1)
cj_2_reattempt = reattempt_stats("CJ", 2)



# ----------------------------------- Jumps ---------------------------------- #

# After a make or miss, what's the average jump? Does it vary by bodyweight?

def jump_stats(lift, n):

   l0 = f"{lift} Attempt {str(n-1)}"
   l1 = f"{lift} Attempt {str(n)}"
   l2 = f"{lift} Attempt {str(n+1)}"
   a0 = f"{lift} Attempt Make {str(n-1)}"
   a1 = f"{lift} Attempt Make {str(n)}"
   a2 = f"{lift} Attempt Make {str(n+1)}"


   # ------------------------------- After a make ------------------------------- #

   # Get only rows where the attempt was successful
   sub_make = data[data[a1]].copy()
   # Make sure the next row isn't NA
   sub_make = sub_make[~pd.isna(sub_make[a2])].copy()

   sub_make["jump"] = sub_make[l2] - sub_make[l1]


   # -------------------------------- Afer a miss ------------------------------- #
   sub_miss = data[~data[a1]].copy()
   sub_miss = sub_miss[~pd.isna(sub_miss[a2])].copy()

   sub_miss["jump"] = sub_miss[l2] - sub_miss[l1]

   # Version that ONLY looks at those that bumped up after the miss
   sub_miss_up = sub_miss[sub_miss[l2] > sub_miss[l1]].copy()


   return pd.Series({
      "Average jump after make": sub_make["jump"].mean(),
      "Median jump after make": sub_make["jump"].median(),
      "Average jump after miss": sub_miss["jump"].mean(),
      "Median jump after miss": sub_miss["jump"].median(),
      "Average jump after miss and bump": sub_miss_up["jump"].mean(),
      "Median jump after miss and jump": sub_miss_up["jump"].median()
   })



snatch_1_jump = jump_stats("Snatch", 1)
snatch_2_jump = jump_stats("Snatch", 2)
cj_1_jump = jump_stats("CJ", 1)
cj_2_jump = jump_stats("CJ", 2)





# ---------------------------------------------------------------------------- #
#                             Manual decision tree                             #
# ---------------------------------------------------------------------------- #

# subset to only rows where all 6 attempts were taken
full = data[
   (~pd.isna(data["Snatch Attempt Make 1"])) &
   (~pd.isna(data["Snatch Attempt Make 2"])) &
   (~pd.isna(data["Snatch Attempt Make 3"])) &
   (~pd.isna(data["CJ Attempt Make 1"])) &
   (~pd.isna(data["CJ Attempt Make 2"])) &
   (~pd.isna(data["CJ Attempt Make 3"])) 
].copy()


# Calculate pct improvement for snatch, cj, and total
full["pct_improvement_snatch"] = np.where(pd.isna(full["Snatch Best"]), 0, (full["Snatch Best"] - full["Snatch Attempt 1"]) / full["Snatch Attempt 1"] + 1)
full["pct_improvement_cj"] = np.where(pd.isna(full["CJ Best"]), 0, (full["CJ Best"] - full["CJ Attempt 1"]) / full["CJ Attempt 1"] + 1)


# Create state columns
full["s1_state"] = np.where(
   full["Snatch Attempt Make 1"],
   "make",
   np.where(
      full["Snatch Attempt 2"] > full["Snatch Attempt 1"],
      "miss_bump",
      "miss_retake"
   )
)

full["s2_state"] = np.where(
   full["Snatch Attempt Make 2"],
   "make",
   np.where(
      full["Snatch Attempt 3"] > full["Snatch Attempt 2"],
      "miss_bump",
      "miss_retake"
   )
)

full["s3_state"] = np.where(
   full["Snatch Attempt Make 3"],
   "make",
   "miss"
)

full["c1_state"] = np.where(
   full["CJ Attempt Make 1"],
   "make",
   np.where(
      full["CJ Attempt 2"] > full["CJ Attempt 1"],
      "miss_bump",
      "miss_retake"
   )
)

full["c2_state"] = np.where(
   full["CJ Attempt Make 2"],
   "make",
   np.where(
      full["CJ Attempt 3"] > full["CJ Attempt 2"],
      "miss_bump",
      "miss_retake"
   )
)

full["c3_state"] = np.where(
   full["CJ Attempt Make 3"],
   "make",
   "miss"
)

# summary using all the groups
snatch_summary = full.groupby(["s1_state", "s2_state", "s3_state"]).agg(
   n = ("Name", "count"),
   p_improvement_mean = ("pct_improvement_snatch", "mean"),
   p_improvement_median = ("pct_improvement_snatch", "median"),
).reset_index()

cj_summary = full.groupby(["c1_state", "c2_state", "c3_state"]).agg(
   n = ("Name", "count"),
   p_improvement_mean = ("pct_improvement_cj", "mean"),
   p_improvement_median = ("pct_improvement_cj", "median"),
).reset_index()

full_summary = full.groupby(["s1_state", "s2_state", "s3_state", "c1_state", "c2_state", "c3_state"]).agg(
   n = ("Name", "count")
).reset_index()

# summary for specific outcomes
snatch_1_summary = full.groupby("s1_state").agg(
   n = ("Name", "count"),
   p_improvement_mean = ("pct_improvement_snatch", "mean"),
   p_improvement_median = ("pct_improvement_snatch", "median"),
).reset_index()

snatch_2_summary = full.groupby(["s1_state", "s2_state"]).agg(
   n = ("Name", "count"),
   p_improvement_mean = ("pct_improvement_snatch", "mean"),
   p_improvement_median = ("pct_improvement_snatch", "median"),
).reset_index()

cj_1_summary = full.groupby("c1_state").agg(
   n = ("Name", "count"),
   p_improvement_mean = ("pct_improvement_cj", "mean"),
   p_improvement_median = ("pct_improvement_cj", "median"),
).reset_index()






# ---------------------------------------------------------------------------- #
#                              Mann Whitney U Test                             #
# ---------------------------------------------------------------------------- #

# --------------------------------- snatch 1 --------------------------------- #
s1b = full[full["s1_state"] == "miss_bump"]["pct_improvement_snatch"].copy()
s1r = full[full["s1_state"] == "miss_retake"]["pct_improvement_snatch"].copy()
u_s1, p_s1 = mannwhitneyu(s1b, s1r)


# --------------------------------- snatch 2 --------------------------------- #

# scenario where the first snatch was a make
s2b_make = full[
   (full["s1_state"] == "make") & 
   (full["s2_state"] == "miss_bump")
]["pct_improvement_snatch"].copy()

s2r_make = full[
   (full["s1_state"] == "make") & 
   (full["s2_state"] == "miss_retake")
]["pct_improvement_snatch"].copy()

u_s2_make, p_s2_make = mannwhitneyu(s2b_make, s2r_make)

# scenario where the first snatch was a miss and bump
s2b_bump = full[
   (full["s1_state"] == "miss_bump") & 
   (full["s2_state"] == "miss_bump")
]["pct_improvement_snatch"].copy()

s2r_bump = full[
   (full["s1_state"] == "miss_bump") & 
   (full["s2_state"] == "miss_retake")
]["pct_improvement_snatch"].copy()

u_s2_bump, p_s2_bump = mannwhitneyu(s2b_bump, s2r_bump)

# scenario where the first snatch was a miss and retake
s2b_retake = full[
   (full["s1_state"] == "miss_retake") & 
   (full["s2_state"] == "miss_bump")
]["pct_improvement_snatch"].copy()

s2r_retake = full[
   (full["s1_state"] == "miss_retake") & 
   (full["s2_state"] == "miss_retake")
]["pct_improvement_snatch"].copy()

u_s2_retake, p_s2_retake = mannwhitneyu(s2b_retake, s2r_retake)


