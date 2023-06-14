import calendar
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt


#Variables
year = 2023
solarArraykWp=81
batteryCapacitykWh=75


loadImport = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\load.csv")
tariffStructure = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariffStructure.csv")

developerX=1
if developerX==0:

    #imports and starting tables

    summerMonths = [1, 2, 3, 4, 11, 12]

    tariffs=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariff.csv")
    solarProfile=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\solarprofile.csv")



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

#---------------------------todo get days empty as a summary
print(df.columns)
daysEmpty = df.groupby('Month').apply(lambda x: sum((x['BatterykWh'] == 0)))
listOfMonths=[1,2,3,4,5,6,7,8,9,10,11,12]
print(f'days Empty{daysEmpty}')

# Plot the graph
plt.bar(listOfMonths,daysEmpty)
plt.xlabel('Month')
plt.ylabel('Days')
plt.title('Days Battery is empty in Month ')
plt.show()


#-------------------------------

#todo print chart
# Assuming the DataFrame is named 'df' and has a 'Date' column and a numeric column to plot
import matplotlib.pyplot as plt

# Define the range of months and days
start_month = 4
end_month = 4
days_in_month = 31  # Assuming maximum of 31 days in a month

# Create a figure and axes for the plot
fig, ax = plt.subplots()

# Iterate through each month
for month in range(start_month, end_month+1):
    # Filter the DataFrame for the selected month
    df_month = df[df['Month'] == month]

    # Iterate through each day in the month
    for day in range(1, days_in_month+1):
        # Filter the DataFrame for the selected day
        df_day = df_month[df_month['Day'] == day]

        # Plot the graph for the day
        ax.plot(df_day['Hour'], df_day['BatterykWh'], label='Month {}, Day {}'.format(month, day))

# Set the x-axis label, y-axis label, and plot title
ax.set_xlabel('Hour')
ax.set_ylabel('kWh')
ax.set_title('Graphs for All Days in Month{}'.format(month))


# Place the legend outside the plot to the right
#ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# Display the plot
plt.show()
#__________________________________________________




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
#print(summary_with_total)
#print(df.head())

#####TKINTER GUI
#____________________________________________________

def show_data_load():
    # Read the CSV file
    global loadImport
    dfLoad = loadImport.copy()

    # Clear existing rows in the tree
    tree.delete(*tree.get_children())

    # Insert the column headers
    tree['columns'] = dfLoad.columns.tolist()
    tree.heading("#0", text="Index")
    for column in dfLoad.columns.tolist():
        tree.heading(column, text=column)
        tree.column(column, width=100)

    # Insert the data rows
    for index, row in dfLoad.iterrows():
        tree.insert("", "end", text=index, values=row.tolist())

def close_show_window():
    # Clear existing rows in the tree
    tree.delete(*tree.get_children())

def open_new_window():
    # Read the CSV file
    global tariffStructure
    dfLoad = tariffStructure.copy()

    # Clear existing rows in the tree
    tree.delete(*tree.get_children())

    # Insert the column headers
    tree['columns'] = tariffStructure.columns.tolist()
    tree.heading("#0", text="Index")
    for column in tariffStructure.columns.tolist():
        tree.heading(column, text=column)
        tree.column(column, width=100)

    # Insert the data rows
    for index, row in dfLoad.iterrows():
        tree.insert("", "end", text=index, values=row.tolist())

all_dataframes = [(name, var) for name, var in locals().items() if isinstance(var, pd.DataFrame)]

def summary_window():
    # Read the CSV file
    global summary_with_total
    print(summary_with_total.index)
    dfLoad = summary_with_total.copy()

    # Clear existing rows in the tree
    tree.delete(*tree.get_children())

    # Insert the column headers
    tree['columns'] = ['#0'] + summary_with_total.columns.tolist()  # Include index column
    tree.heading("#0", text="Index")
    for column in summary_with_total.columns.tolist():
        tree.heading(column, text=column)
        tree.column(column, width=80)

    # Insert the data rows
    for index, row in dfLoad.iterrows():
        tree.insert("", "end", text=index, values=[index] + row.tolist())

all_dataframes = [(name, var) for name, var in locals().items() if isinstance(var, pd.DataFrame)]


# Print the names of the DataFrames
for name, _ in all_dataframes:
    print(name)

window = tk.Tk()
window.title("CSV Viewer")
# Set the window size
window.geometry("800x600")  # Width x Height

tree = ttk.Treeview(window)

scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)

button_show_data = tk.Button(window, text="Load", command=show_data_load)
button_open_new_window = tk.Button(window, text="Tariff Structure", command=open_new_window)
button_open_summary = tk.Button(window, text="Summary", command=summary_window)
button_close_show_window = tk.Button(window, text="Close Show Window", command=close_show_window)
button_close_app = tk.Button(window, text="Close Application", command=window.quit)

button_show_data.pack(pady=10)
button_open_new_window.pack(pady=10)
button_open_summary.pack(pady=10)
button_close_show_window.pack(pady=10)
button_close_app.pack(pady=10)
tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Hide the index column
tree["show"] = "headings"

window.mainloop()

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