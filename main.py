import calendar
import pandas as pd
from datetime import datetime

loadImport = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\load.csv", header=0)
summerMonths = [1, 2, 3, 4, 11, 12]

year = 2023

# Get all the months in the year
months = [calendar.month_name[i] for i in range(1, 13)]

# Create a list of all days in the year
days_in_year = [(month, day) for month in range(1, 13) for day in range(1, calendar.monthrange(year, month)[1] + 1)]

# Create a DataFrame
df = pd.DataFrame(days_in_year, columns=['Month', 'Day'])

# Add the 'Season' column to the DataFrame
summerWinter = []
weekDay=[]
for _, row in df.iterrows():
    month = row['Month']
    day=row['Day']
    myDate=str(f"{year}-{month}-{day}")
    dayOfWeek=datetime.strptime(myDate, "%Y-%m-%d")
    weekDay.append(dayOfWeek.weekday())
    if month in summerMonths:
        season = "Summer"
    else:
        season = "Winter"
    summerWinter.append(season)
df['Season'] = summerWinter
df['Weekday']=weekDay


print(df)



#VARIABLES
"""
batteryCapacity=2

df=pd.DataFrame({'hour':[1,2,3,4],'load':[1,1,2,1],  'solar':[0,1,1,0]})
df['load']=df['load'].astype(float)
batterySOCList=[]
gridGenDemandList=[]
export=[]
for i in range(len(df['hour'])):
    batteryCapacityStart=batteryCapacity
    batteryCapacity=batteryCapacity-df['load'][i]+ df['solar'][i]
    if batteryCapacity<0:
        gridGenDemand=df['load'][i]- df['solar'][i]-batteryCapacityStart
        batteryCapacity=0
    else:
        gridGenDemand=0
    batterySOCList.append(batteryCapacity)
    gridGenDemandList.append(gridGenDemand)

df['batterySOC']=batterySOCList
df['gridGenDemand']=gridGenDemandList

print(df)
"""