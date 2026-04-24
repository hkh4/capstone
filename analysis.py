import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree import plot_tree
from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt
import seaborn as sns

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


# Chart
snatch = make_miss.iloc[:3].values * 100
cj = make_miss.iloc[3:].values * 100

# x location
x = np.array([0, 1])  
width = 0.22

fig, ax = plt.subplots(figsize=(8, 5))

ax.bar(x - width, [snatch[0], cj[0]], width, label='Attempt 1')
ax.bar(x,         [snatch[1], cj[1]], width, label='Attempt 2')
ax.bar(x + width, [snatch[2], cj[2]], width, label='Attempt 3')

# Labels and formatting
ax.set_xlabel('Lift')
ax.set_ylabel('Make Rate (%)')
ax.set_title('Make Rate by Lift and Attempt')
ax.set_xticks(x)
ax.set_xticklabels(['Snatch', 'Clean & Jerk'])
ax.legend()

plt.tight_layout()

plt.savefig("charts/make_rate_by_lift.png", dpi=300, bbox_inches='tight')

plt.show()




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
u_s1_percent = u_s1 / (len(s1b) * len(s1r))


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
u_s2_make_percent = u_s2_make / (len(s2b_make) * len(s2r_make))

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
u_s2_bump_percent = u_s2_bump / (len(s2b_bump) * len(s2r_bump))

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
u_s2_retake_percent = u_s2_retake / (len(s2b_retake) * len(s2r_retake))




# --------------------------------- cj 1 --------------------------------- #
c1b = full[full["c1_state"] == "miss_bump"]["pct_improvement_cj"].copy()
c1r = full[full["c1_state"] == "miss_retake"]["pct_improvement_cj"].copy()
u_c1, p_c1 = mannwhitneyu(c1b, c1r)
u_c1_percent = u_c1 / (len(c1b) * len(c1r))


# --------------------------------- cj 2 --------------------------------- #

# scenario where the first cj was a make
c2b_make = full[
   (full["c1_state"] == "make") & 
   (full["c2_state"] == "miss_bump")
]["pct_improvement_cj"].copy()

c2r_make = full[
   (full["c1_state"] == "make") & 
   (full["c2_state"] == "miss_retake")
]["pct_improvement_cj"].copy()

u_c2_make, p_c2_make = mannwhitneyu(c2b_make, c2r_make)
u_c2_make_percent = u_c2_make / (len(c2b_make) * len(c2r_make))

# scenario where the first cj was a miss and bump
c2b_bump = full[
   (full["c1_state"] == "miss_bump") & 
   (full["c2_state"] == "miss_bump")
]["pct_improvement_cj"].copy()

c2r_bump = full[
   (full["c1_state"] == "miss_bump") & 
   (full["c2_state"] == "miss_retake")
]["pct_improvement_cj"].copy()

u_c2_bump, p_c2_bump = mannwhitneyu(c2b_bump, c2r_bump)
u_c2_bump_percent = u_c2_bump / (len(c2b_bump) * len(c2r_bump))

# scenario where the first cj was a miss and retake
c2b_retake = full[
   (full["c1_state"] == "miss_retake") & 
   (full["c2_state"] == "miss_bump")
]["pct_improvement_cj"].copy()

c2r_retake = full[
   (full["c1_state"] == "miss_retake") & 
   (full["c2_state"] == "miss_retake")
]["pct_improvement_cj"].copy()

u_c2_retake, p_c2_retake = mannwhitneyu(c2b_retake, c2r_retake)
u_c2_retake_percent = u_c2_retake / (len(c2b_retake) * len(c2r_retake))



# -------------------------- Number of attempts made ------------------------- #

full["made"] = (full["Snatch Attempt Make 1"].astype(float)) + full["Snatch Attempt Make 2"]  + full["Snatch Attempt Make 3"] + full["CJ Attempt Make 1"] + full["CJ Attempt Make 2"] + full["CJ Attempt Make 3"]
makes = full["made"].value_counts().reset_index()
makes["p"] = makes["count"] / len(full)

# Sort
makes_sorted = makes.sort_values('made')

sizes = makes_sorted['p']
labels = [str(int(m)) for m in makes_sorted['made']]

# Function to hide tiny percentages
def autopct_func(pct):
    return f'{pct:.1f}%' if pct > 5 else ''  # only show if >5%

fig, ax = plt.subplots(figsize=(6, 6))

ax.pie(
    sizes,
    labels=labels,
    autopct=autopct_func,
    startangle=90
)

ax.set_title('Number of Made Attempts (Out of 6)')

plt.tight_layout()

# Save
plt.savefig("charts/makes_distribution_pie.png", dpi=300, bbox_inches='tight')

plt.show()




# ------------------ Make Probability By Attempt Difficulty ------------------ #

# Make percentage based on % over opener
full["s1p"] = 0
full["s2p"] = (full["Snatch Attempt 2"] - full["Snatch Attempt 1"]) / full["Snatch Attempt 1"]
full["s3p"] = (full["Snatch Attempt 3"] - full["Snatch Attempt 1"]) / full["Snatch Attempt 1"]
full["c1p"] = 0
full["c2p"] = (full["CJ Attempt 2"] - full["CJ Attempt 1"]) / full["CJ Attempt 1"]
full["c3p"] = (full["CJ Attempt 3"] - full["CJ Attempt 1"]) / full["CJ Attempt 1"]

full["s2p"] = full["s2p"].round(3)
full["s3p"] = full["s3p"].round(3)
full["c2p"] = full["c2p"].round(3)
full["c3p"] = full["c3p"].round(3)

# melt into long form
s1 = full[["s1p", "Snatch Attempt Make 1"]].copy()
s2 = full[["s2p", "Snatch Attempt Make 2"]].copy()
s3 = full[["s3p", "Snatch Attempt Make 3"]].copy()
c1 = full[["c1p", "CJ Attempt Make 1"]].copy()
c2 = full[["c2p", "CJ Attempt Make 2"]].copy()
c3 = full[["c3p", "CJ Attempt Make 3"]].copy()

s1.columns = ["p", "make"]
s2.columns = ["p", "make"]
s3.columns = ["p", "make"]
c1.columns = ["p", "make"]
c2.columns = ["p", "make"]
c3.columns = ["p", "make"]

full_percent = pd.concat([s1,s2,s3,c1,c2,c3])
full_percent["make"] = full_percent["make"].astype("float")
make_summary = full_percent.groupby("p").agg(
   avg = ("make", "mean")
).reset_index()

fig, ax = plt.subplots(figsize=(10, 6))

sns.regplot(
   x="p",
   y="make",
   data=full_percent,
   logistic=True,
   scatter_kws={"alpha": 0.5, "s": 5},
   line_kws={"color": "red", "lw": 2},
   ax=ax
)

plt.xlim(0, 0.4)
ax.set_xlabel("% Increase From Opener", fontsize=16)
ax.set_ylabel("Probability of Success", fontsize=16)
plt.savefig("charts/regression.png", dpi=600)



