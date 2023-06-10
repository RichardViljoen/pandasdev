import calendar
import pandas as pd
from datetime import datetime

#Variables
year = 2023
solarArraykWp=100
batteryCapacitykWh=5

developerX=0
if developerX==0:

    #imports and starting tables
    loadImport = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\load.csv")
    summerMonths = [1, 2, 3, 4, 11, 12]
    tariffStructure = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariffStructure.csv")
    tariffs=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariff.csv")
    solarProfile=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\solarprofile.csv")


    #print(tariffs[(tariffs['Season'] == "Low Demand") & (tariffs['Period'] == "Peak")])
    #bob = pd.DataFrame(tariffStructure[(tariffStructure['Low-High'] == "Low Demand") ])
    #print(bob['2'])


    # Get all the months in the year
    months = [calendar.month_name[i] for i in range(1, 13)]

    # Create a list of all days in the year
    hours_in_year = [(month, day, hour) for month in range(1, 13) for day in range(1, calendar.monthrange(year, month)[1] + 1) for hour in range(24)]

    # Create a DataFrame
    df = pd.DataFrame(hours_in_year, columns=['Month', 'Day', 'Hour'])

    # Add the 'Season' column to the DataFrame
    summerWinter = []
    weekDay=[]
    hourList = []
    tariffPeriod=[]
    tariffExRate=[]
    tariffImRate=[]
    load=[]

    for _, row in df.iterrows():
        month = row['Month']
        day=row['Day']
        hour=row['Hour']
        myDate=str(f"{year}-{month}-{day}")
        dayOfWeek=datetime.strptime(myDate, "%Y-%m-%d")
        weekDay.append(dayOfWeek.weekday()+1)
        dayOfWeek=dayOfWeek.weekday()+1
        if month in summerMonths:
            season = "Low Demand"
        else:
            season = "High Demand"
        summerWinter.append(season)
        #Add the tariff rate
        hourTariffPeriod = tariffStructure.loc[(tariffStructure['Low-High'] == season) & (tariffStructure['Hour'] == hour), str(dayOfWeek)].values[0]
        tariffPeriod.append(hourTariffPeriod)

        # Add the tariff price export
        hourExportTariff = tariffs.loc[(tariffs['Season'] == season) & (tariffs['Period'] == hourTariffPeriod), 'Export'].values[0]
        hourImportTariff = tariffs.loc[(tariffs['Season'] == season) & (tariffs['Period'] == hourTariffPeriod), 'Import'].values[0]
        tariffExRate.append(hourExportTariff)
        tariffImRate.append(hourImportTariff)


        # Add the load profile
        hourload = loadImport.loc[(loadImport['Hour'] == hour), season].values[0]
        load.append(hourload)

    df['Season'] = summerWinter
    df['Weekday']=weekDay
    df['Tarrif Period']=tariffPeriod
    df['Import Rate']=tariffImRate
    df['Export Rate']=tariffExRate
    df['Load']=load
    #print("%.2f" % floatNumber)
    df['solar']=solarProfile['AC System Output (W)']*solarArraykWp/1000

    #CALCULATIONS
    #for Grid/battery calc
    df['for Grid/Batt']=df['solar']-df['Load']

    #battery and grid impact
    batterykWh=[]
    gridkWh=[]
    newBatkWh=batteryCapacitykWh
    for i in range(len(df['Month'])):
        if -df['for Grid/Batt'][i]>newBatkWh:
            newGridkWh=newBatkWh+df['for Grid/Batt'][i]
            newBatkWh=0
        else:
            newBatkWh=newBatkWh+df['for Grid/Batt'][i]
            newGridkWh=0
            if newBatkWh>batteryCapacitykWh:
                newGridkWh=newBatkWh-batteryCapacitykWh
                newBatkWh=batteryCapacitykWh

        batterykWh.append(newBatkWh)
        gridkWh.append(newGridkWh)
    df['BatterykWh']=batterykWh
    df['GridkWh']=gridkWh
    df['Excl Solar Cost']=df['Load']*df['Import Rate']/100
    LgridImportkWh=[]
    LgridExportkWh= []
    for _,row in df.iterrows():
        grid=row['GridkWh']
        if grid>0:
            gridExportkWh=grid
            gridImportkWh=0
        else:
            gridExportkWh = 0
            gridImportkWh = grid
        LgridExportkWh.append(gridExportkWh)
        LgridImportkWh.append(gridImportkWh)
    df['Grid Import kWh']=LgridImportkWh
    df['Grid Export kWh']=LgridExportkWh

    df.to_csv('output.csv', index=False)

else:
    setup=pd.read_csv(r'C:\Users\shanr\PycharmProjects\Pandas\output.csv')
    df=pd.DataFrame(setup)

df['Import Cost']=df['Grid Import kWh']*df['Import Rate']*-1/100
df['Export Revenue']=df['Grid Export kWh']*df['Export Rate']/100

#df.loc[df['Month'] == 1, 'ColumnName']
#Excl Solar Cost,Grid Import kWh,Grid Export kWh
summary = df.groupby('Month').agg({'Load': 'sum', 'Excl Solar Cost': 'sum', 'Grid Import kWh': 'sum', 'Grid Export kWh': 'sum','Import Cost': 'sum', 'Export Revenue': 'sum'})
summary["Cost Saving"]=summary['Excl Solar Cost']-summary['Import Cost']
summary['Total Impact'] = summary['Cost Saving']+summary['Export Revenue']

total_row = summary.sum(numeric_only=True)  # Calculate the total row
summary_with_total = summary._append(total_row, ignore_index=True)  # Append the total row to the summary DataFrame

columns_to_format = ['Excl Solar Cost', 'Import Cost', 'Export Revenue', 'Cost Saving', 'Total Impact']
summary_with_total[columns_to_format] = summary_with_total[columns_to_format].applymap(lambda x: "R{:,.0f}".format(x))

columns_to_format = ['Load', 'Grid Import kWh', 'Grid Export kWh']
summary_with_total[columns_to_format] = summary_with_total[columns_to_format].applymap(lambda x: "{:,.0f}".format(x))

summary_with_total = summary_with_total.rename(index={summary_with_total.index[-1]: 'Total'})

summary_with_total.to_csv('summary.csv', index=False)
print(summary_with_total)
#print(df.head())


#OLD
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