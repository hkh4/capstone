import pandas as pd
import numpy as np

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

make_miss = data.groupby("Gender").agg(
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

   l1 = f"{lift} Attempt {str(n)}"
   l2 = f"{lift} Attempt {str(n+1)}"
   a1 = f"{lift} Attempt Make {str(n)}"
   a2 = f"{lift} Attempt Make {str(n+1)}"

   # Get only rows where the attempt missed 
   sub = data[~data[a1]].copy()


snatch_1_reattempt = reattempt_stats("Snatch", "1")





