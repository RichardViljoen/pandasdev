import calendar
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from PIL import Image, ImageTk



#Variables
year = 2023
dfSystemSettings = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\system_settings.csv")
solarArraykWp=dfSystemSettings.iloc[0,0]
batteryCapacitykWh=dfSystemSettings.iloc[1,0]


loadImport = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\modifiedcsv.csv")
#loadImport = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\load.csv")
tariffStructure = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariffStructure.csv")



def mainRun(solarArraykWpNew, batteryCapacitykWhNew):
    global solarArraykWp, batteryCapacitykWh
    solarArraykWp, batteryCapacitykWh = solarArraykWpNew, batteryCapacitykWhNew
    #imports and starting tables

    summerMonths = [1, 2, 3, 4, 10, 11, 12]
    print(f"Progress: summer months:{summerMonths}, Solar: {solarArraykWp}kWp, Battery: {batteryCapacitykWh}kWh")

    tariffs=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\tariff.csv")
    solarProfile=pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\solarprofile.csv")

    systemSettings=[solarArraykWp,batteryCapacitykWh]
    dfSystemSettings=pd.DataFrame()
    dfSystemSettings['settings']=systemSettings
    dfSystemSettings.to_csv('system_settings.csv', index=False)

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
    printMonth=-1

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

        if dayOfWeek in [1,7]:
            weekDayType="Weekend"
        else:
            weekDayType="Week"
        # Add the load profile
        loadImportFilter=loadImport[(loadImport['Week Type']==weekDayType)&(loadImport['Hour']==hour)]
        loadImportFilter=loadImportFilter.iloc[:, 2:]
        hourload = loadImportFilter.iloc[0,month-1]
        load.append(hourload)
        if printMonth!=month:
            print(f"Progress: month:{month}")

        printMonth=month

    df['Season'] = summerWinter
    df['Weekday']=weekDay
    df['Tarrif Period']=tariffPeriod
    df['Import Rate']=tariffImRate
    df['Export Rate']=tariffExRate
    df['Load']=load
    df['solar']=solarProfile['AC System Output (W)']*solarArraykWp/1000
    print(f"Progress: df created for {solarArraykWp}kWp,{batteryCapacitykWh}kWh, tariffs and seasons")

    #CALCULATIONS
    #for Grid/battery calc
    df['for Grid/Batt']=df['solar']-df['Load']

    #battery and grid impact
    batterykWh=[]
    gridkWh=[]
    newBatkWh=batteryCapacitykWh

    drainConditionList=['Peak', 'Standard']

    for i in range(len(df['Month'])):
        if -df['for Grid/Batt'][i]>newBatkWh and df['Tarrif Period'][i] in drainConditionList:
            newGridkWh=newBatkWh+df['for Grid/Batt'][i]
            newBatkWh=0
        elif df['Tarrif Period'][i] in drainConditionList:
            newBatkWh=newBatkWh+df['for Grid/Batt'][i]
            newGridkWh=0
            if newBatkWh>batteryCapacitykWh:
                newGridkWh=newBatkWh-batteryCapacitykWh
                newBatkWh=batteryCapacitykWh
        else:
            newGridkWh=df['for Grid/Batt'][i]

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
    df['Import Cost'] = df['Grid Import kWh'] * df['Import Rate'] * -1 / 100
    df['Export Revenue'] = df['Grid Export kWh'] * df['Export Rate'] / 100
    print(f"Progress: Calculations Completed")
    df.to_csv('output.csv', index=False)
    print(f"Progress: output file created")


    summary = df.groupby('Month').agg(
        {'Load': 'sum', 'Excl Solar Cost': 'sum', 'Grid Import kWh': 'sum', 'Grid Export kWh': 'sum',
         'Import Cost': 'sum', 'Export Revenue': 'sum'})
    summary["Cost Saving"] = summary['Excl Solar Cost'] - summary['Import Cost']
    summary['Total Impact'] = summary['Cost Saving'] + summary['Export Revenue']

    total_row = summary.sum(numeric_only=True)  # Calculate the total row
    summary_with_total = summary._append(total_row, ignore_index=True)  # Append the total row to the summary DataFrame

    columns_to_format = ['Excl Solar Cost', 'Import Cost', 'Export Revenue', 'Cost Saving', 'Total Impact']
    summary_with_total[columns_to_format] = summary_with_total[columns_to_format].applymap(
        lambda x: "R{:,.0f}".format(x))

    columns_to_format = ['Load', 'Grid Import kWh', 'Grid Export kWh']
    summary_with_total[columns_to_format] = summary_with_total[columns_to_format].applymap(
        lambda x: "{:,.0f}".format(x))

    summary_with_total = summary_with_total.rename(index={summary_with_total.index[-1]: 'Total'})

    summary_with_total.to_csv('summary.csv', index=False)
    # print(summary_with_total)
    # print(df.head())

def plots():
    global monthPlotVariable, plotMonths, df
    # Get the current date and time
    currentDatetime = datetime.now()
    printDate = currentDatetime.strftime("%Y-%m-%d %H:%M:%S")

    #Set output folder
    outputFolder = 'C:\\Users\\shanr\\PycharmProjects\\Pandas\\venv\\Output Folder\\'

    print("Exporting Plots")
    daysEmptyMonthList=[]
    daysEmptyValueList=[]
    setup = pd.read_csv(r'C:\Users\shanr\PycharmProjects\Pandas\output.csv')
    df = pd.DataFrame(setup)
    for month in df['Month'].unique():
        filteredDf=df[(df['Month']==month)&(df['BatterykWh'] ==0)]
        monthDaysEmpty= filteredDf.groupby('Day').nunique()#.reset_index(name='Count')
        monthDaysEmpty=len(monthDaysEmpty)
        daysEmptyMonthList.append(month)
        daysEmptyValueList.append(monthDaysEmpty)
        #print(month, monthDaysEmpty)

    # Plot the graph
    fig1, ax1= plt.subplots()

    ax1.bar(daysEmptyMonthList,daysEmptyValueList)
    ax1.set_xlabel('Month')
    # Set the number of steps on the x-axis
    ax1.set_xticks(range(13))
    ax1.set_ylabel('Days')
    #plt.set_suptitle('Days Battery is empty in Month ',fontsize=16)
    ax1.set_title(f'{solarArraykWp}kWp & {batteryCapacitykWh}kWh & {printDate}',fontsize=12)

    filename=f"BatteryDaysEmpty.png"
    plt.savefig(f"{outputFolder}{filename}", dpi=100)
    print("Battery Days Exported to Output Folder")


    columnsToPlot = [['solar','Solar kWh'], ['BatterykWh', 'Battery kWh' ], ['Grid Import kWh', 'Grid Import kWh']] #syntax: column name, Graph Name
    for item in columnsToPlot:
        plt.figure()

        # Create a figure and axes for the plot
        fig, ax = plt.subplots(4, 3, sharex='col', sharey='row', figsize=(12, 12))

        # Set the main heading for the entire figure
        fig.text(0.5, 0.92, f"{solarArraykWp} kWp & {batteryCapacitykWh} kWh - {printDate}", ha='center', fontsize=12)
        fig.suptitle(item[1], fontsize=16)
        plt.title(f"{solarArraykWp}kWp & {batteryCapacitykWh}kWh", y=1.05, fontsize=12)

        # Define the range of months and days

        for aMonth in range(1, 13):
            start_month = aMonth
            end_month = aMonth
            days_in_month = 31  # Assuming maximum of 31 days in a month

            # Iterate through each month
            for month in range(start_month, end_month + 1):
                # Filter the DataFrame for the selected month
                df_month = df[df['Month'] == month]

                # Iterate through each day in the month
                for day in range(1, days_in_month + 1):
                    # Filter the DataFrame for the selected day
                    df_day = df_month[df_month['Day'] == day]

                    # Plot the graph for the day
                    row = (aMonth - 1) // 3  # Calculate the row index
                    col = (aMonth - 1) % 3  # Calculate the column index
                    ax[row, col].plot(df_day['Hour'], df_day[item[0]], label='Month {}, Day {}'.format(month, day))

                # Set the x-axis label, y-axis label, and plot title for each subplot
                row = (aMonth - 1) // 3  # Calculate the row index
                col = (aMonth - 1) % 3  # Calculate the column index
                ax[row, col].set_xlabel('Hour')
                ax[row, col].set_ylabel('kWh')
                ax[row, col].set_title('Month {}'.format(aMonth))

        # Set the y-axis label for each row
        for row in range(4):
            ax[row, 0].set_ylabel('kWh')

        # Set the x-axis label for each column
        for col in range(3):
            ax[3, col].set_xlabel('Hour')

        # Adjust the spacing between subplots
        plt.subplots_adjust(wspace=0.2, hspace=0.4)

        # Display the plot

        plt.savefig(f'{outputFolder}{item[1]}.png')
        print(f"{item[1]} exported to Output Folder")
        plt.close()
        #plt.show()
    print("Exports Complete")

    #__________________________________________________


#####TKINTER GUI#____________________________________________________

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
    summary_with_total = pd.read_csv(r"C:\Users\shanr\PycharmProjects\Pandas\summary.csv")
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
button_plots = tk.Button(window, text="Export Plots", command=plots)

#----------------------- Create labels and input fields
solar_label = tk.Label(window, text="Solar Array (kWp):")
solar_label.pack()
solar_entry = tk.Entry(window)
solar_entry.pack()

battery_label = tk.Label(window, text="Battery Capacity (kWh):")
battery_label.pack()
battery_entry = tk.Entry(window)
battery_entry.pack()

# Set the default values in the input fields
solar_entry.insert(0, solarArraykWp)  # Previous default value
battery_entry.insert(0, batteryCapacitykWh)  # Previous default value

# Create the submit button
def on_submit():
    global solarArraykWp, batteryCapacitykWh
    # Get user input values
    solar_input = solar_entry.get()
    battery_input = battery_entry.get()

    # Validate and convert input values
    try:
        solarArraykWp = float(solar_input)
        batteryCapacitykWh = float(battery_input)

        # Call mainRun function with the user input values
        mainRun(solarArraykWp, batteryCapacitykWh)

        print("Success", "Calculation completed successfully!")
    except ValueError:
        print("Error", "Invalid input. Please enter numeric values for solar array and battery capacity.")

submit_button = tk.Button(window, text="Submit", command=on_submit)
submit_button.pack()
#----------------------- Create labels and input fields




button_close_app = tk.Button(window, text="Close Application", command=window.quit)

button_plots.pack(pady=10)
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