import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import csv
from openpyxl import load_workbook
from pandas import ExcelWriter

def FunkyGraphs(df):
    df.plot(kind='bar', x='Date', y='Steps', color='red')
    plt.show()


def export_dataframe_to_excel(fullpath, df, startrow, startcol):
    """
    Append dataframe to excel file
    """

    writer = pd.ExcelWriter(fullpath)
    df.to_excel(writer, 'Sheet1', startrow, startcol, index=False, header=False)

    writer.save()
    writer.close()
    print('Finished appending data to ' + fullpath)


def export_dataframe_to_csv(fullpath, df):
    """
    Append dataframe to a csv file
    """

    with open(fullpath, 'a', newline='') as f:
        df.to_csv(fullpath, mode='a', index=False, header=False)