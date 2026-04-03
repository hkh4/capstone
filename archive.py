# ------------------------------- Decision tree ------------------------------ #

# Question: after a second attempt miss, is it more advantageous to retake or to bump?
# Look at the best successful lift as a % of first attempt selection
# bomb out = 0%
# first attempt make only = 100%
# third attempt bump up make which is 10% higher than first attempt = 110%

# ds2 = decision tree, snatch, 2nd attempt
ds2 = data[(~data["Snatch Attempt Make 2"]) & (~pd.isna(data["Snatch Attempt Make 3"]))].copy()

# Create a variable that looks at the best lift as a percentage of first attempt
ds2["pct_improvement"] = np.where(pd.isna(ds2["Snatch Best"]), 0, (ds2["Snatch Best"] - ds2["Snatch Attempt 1"]) / ds2["Snatch Attempt 1"] + 1)

# Relative strength, to control for the individual strength of a lifter
#ds2["rel_strength"] = ds2["Snatch Attempt 2"] / ds2["Snatch Attempt 1"]

# Turn snatch attempt 1 make/miss into binary
ds2["Snatch Attempt Make 1"] = ds2["Snatch Attempt Make 1"].astype("float") 

# Strategy - did they bump or retake?
ds2["strategy"] = np.where(ds2["Snatch Attempt 3"] > ds2["Snatch Attempt 2"], "bump", "retake")

# Category: groups of 10
ds2["category_num"] = ds2["Category"].str.extract(r"(\d+)")
ds2["category_num"] = ds2["category_num"].astype(int)
ds2["category_group"] = np.floor((ds2["category_num"] / 10)) * 10

# Turn into numeric values
ds2 = pd.get_dummies(ds2, columns=["Gender", "strategy"], drop_first=True)

#x = ds2[["Gender_Women", "category_group", "rel_strength", "Snatch Attempt Make 1", "strategy_retake"]].copy()
x = ds2[["Gender_Women", "category_group", "Snatch Attempt Make 1", "strategy_retake"]].copy()

# Run decision tree
y = ds2["pct_improvement"]

model = DecisionTreeRegressor(max_depth=3, random_state=42, min_samples_split=40, min_samples_leaf=20)
model.fit(x, y)

plt.figure(figsize=(15,8))
plot_tree(model, feature_names=x.columns, filled=True, precision=5)
plt.show()





# ------------------------------ Version for cj2 ----------------------------- #

# dc2 = decision tree, cj, 2nd attempt
dc2 = data[(~data["CJ Attempt Make 2"]) & (~pd.isna(data["CJ Attempt Make 3"]))].copy()

# Create a variable that looks at the best lift as a percentage of first attempt
dc2["pct_improvement"] = np.where(pd.isna(dc2["CJ Best"]), 0, (dc2["CJ Best"] - dc2["CJ Attempt 1"]) / dc2["CJ Attempt 1"] + 1)

# Relative strength, to control for the individual strength of a lifter
dc2["rel_strength"] = dc2["CJ Attempt 2"] / dc2["CJ Attempt 1"]

# Turn CJ attempt 1 make/miss into binary
dc2["CJ Attempt Make 1"] = dc2["CJ Attempt Make 1"].astype("float") 

# Strategy - did they bump or retake?
dc2["strategy"] = np.where(dc2["CJ Attempt 3"] > dc2["CJ Attempt 2"], "bump", "retake")

# Category: groups of 10
dc2["category_num"] = dc2["Category"].str.extract(r"(\d+)")
dc2["category_num"] = dc2["category_num"].astype(int)
dc2["category_group"] = np.floor((dc2["category_num"] / 10)) * 10

# Turn into numeric values
dc2 = pd.get_dummies(dc2, columns=["Gender", "strategy"], drop_first=True)

x = dc2[["Gender_Women", "category_group", "rel_strength", "CJ Attempt Make 1", "strategy_retake"]].copy()

# Run decision tree
y = dc2["pct_improvement"]

model = DecisionTreeRegressor(max_depth=3, random_state=42, min_samples_split=40, min_samples_leaf=20)
model.fit(x, y)

plt.figure(figsize=(15,8))
plot_tree(model, feature_names=x.columns, filled=True, precision=5)
plt.show()







# ------------------------- Snatch first attempt miss ------------------------ #

# ds1 = decision tree, snatch, 1st attempt
ds1 = data[(~data["Snatch Attempt Make 1"]) & (~pd.isna(data["Snatch Attempt Make 2"]))].copy()

# Create a variable that looks at the best lift as a percentage of first attempt
ds1["pct_improvement"] = np.where(pd.isna(ds1["Snatch Best"]), 0, (ds1["Snatch Best"] - ds1["Snatch Attempt 1"]) / ds1["Snatch Attempt 1"] + 1)

# # Relative strength, to control for the individual strength of a lifter
# ds1["rel_strength"] = ds1["Snatch Attempt 2"] / ds1["Snatch Attempt 1"]

# Turn snatch attempt 1 make/miss into binary
ds1["Snatch Attempt Make 1"] = ds1["Snatch Attempt Make 1"].astype("float") 

# Strategy - did they bump or retake?
ds1["strategy"] = np.where(ds1["Snatch Attempt 2"] > ds1["Snatch Attempt 1"], "bump", "retake")

# Category: groups of 10
ds1["category_num"] = ds1["Category"].str.extract(r"(\d+)")
ds1["category_num"] = ds1["category_num"].astype(int)
ds1["category_group"] = np.floor((ds1["category_num"] / 10)) * 10

# Turn into numeric values
ds1 = pd.get_dummies(ds1, columns=["Gender", "strategy"], drop_first=True)

x = ds1[["Gender_Women", "category_group", "Snatch Attempt Make 1", "strategy_retake"]].copy()

# Run decision tree
y = ds1["pct_improvement"]

model = DecisionTreeRegressor(max_depth=3, random_state=42, min_samples_split=40, min_samples_leaf=20)
model.fit(x, y)

plt.figure(figsize=(15,8))
plot_tree(model, feature_names=x.columns, filled=True, precision=5)
plt.show()


