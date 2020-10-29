import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np
import statsmodels.api as sm

data = pd.read_csv("filmdeathcounts.csv")
pd.set_option('display.max_columns', 500)

# body_per_min
data["body_per_min"] = data["Body_Count"] / data["Length_Minutes"]
print("Bodies per minute.")
print(data.loc[1:544,['Film', 'body_per_min']])

# body_count hist
data['Body_Count'].plot(kind="hist", edgecolor="black", color="cyan", bins=40)
plt.xlabel("Body_Count")
plt.show()

# mean and series deviation
imdb_mean = data['IMDB_Rating'].mean()
imdb_sd = data['IMDB_Rating'].std()

print("Mean and standard deviation.")
print(imdb_mean, imdb_sd)

# top10
print(data.sort_values(by=['Body_Count'], ascending=False).head(10))
print(data.sort_values(by=['body_per_min'], ascending=False).head(10))

# rating
data['IMDB_Rating'].plot(kind="hist", edgecolor="black", color="cyan", bins=20)
plt.xlabel("IMDB_Rating")
plt.show()

data['imdb_simulation'] = np.random.normal(imdb_mean, imdb_sd, len(data.index))
# simulation hist
data['imdb_simulation'].plot(kind="hist", edgecolor="black", color="cyan", bins=40)
plt.xlabel("imdb_simulation")
plt.show()

#qqplot
sm.qqplot(data['imdb_simulation'], line ='45')
plt.xlabel("imdb_simulation")
plt.show()

sm.qqplot(data['IMDB_Rating'], line ='45')
plt.xlabel("IMDB_Rating")
plt.show()
