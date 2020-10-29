import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

data = pd.read_csv("flats.csv", sep = ',', decimal=',')
data.columns = [col.replace('"', '') for col in data.columns]

"""
print(data.shape)

print(data.head(6))
print(data.head(15))
print(data.tail(6))

print(data.columns)
"""

"""
print(len(data.columns))
print(len(data.filter(items="Місто")))
print(len(data[(data.Місто == "Одеса") & (data.Кімнат == 3)]))

data["Загальна_площа"] = data["Загальна_площа"].str.replace(
    ',', '.'
).astype(float)
newdata = data[(data.Місто == "Львів") & (data.Кімнат == 1)]
print(newdata["Загальна_площа"].median())
"""
print(len(data.loc[data["Місто"] == "Києво-Святошинський"]))
print(data["Загальна_площа"].mean())

# data['Кімнат'].describe()

# data.groupby('Місто').count()

values = data.groupby('Кімнат').size().reset_index(name='Кількість')
x_ax = values['Кімнат'].tolist()
y_ax = values['Кількість'].tolist()

plt.bar(x_ax, y_ax, color='b')
plt.xlabel('Кімнат')
plt.ylabel('Кількість')
plt.show()

values = data.groupby('Загальна_площа').size().reset_index(name='Кількість')
x_ax = values['Загальна_площа'].tolist()
y_ax = values['Кількість'].tolist()
plt.bar(x_ax,y_ax, color='r')
plt.xlabel('Загальна_площа')
plt.ylabel('Кількість')
plt.show()

x = data['Загальна_площа']
plt.hist(x, bins=[i for i in range(0,251,25)], align='mid', color='y')
plt.yticks(np.arange(0, 301, 100))
plt.xticks(np.arange(0, 251, 50))
plt.xlabel('Загальна_площа')
plt.ylabel('Кількість')
plt.show()

x = data['Загальна_площа']
y = data['Ціна']
plt.scatter(x, y, 3, c='g')
plt.yticks(np.arange(0, 12500001, 2500000))
plt.xticks(np.arange(0, 201, 50))
plt.xlabel('Загальна_площа')
plt.ylabel('Ціна')
plt.show()

plt.figure(figsize=(15, 15))
ax=sns.boxplot(y='Місто', x="Ціна",orient='h', data=data, linewidth=2)
plt.show()
