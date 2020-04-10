import fitbit
import fitbit.gather_keys_ouath2 as Oauth2
import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import csv
import datetime
import time
from openpyxl import load_workbook
from pandas import ExcelWriter

# some dates to experiment with...
yesterday = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))
yesterday_with_hyphens = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
today = str(datetime.datetime.now().strftime("%Y%m%d"))


def FunkyGraphs(df):
    df.plot(kind='bar', x='Date', y='Steps', color='red')
    plt.show()


def get_dates(auth2_client, start_date, end_date):
    """
    Retrieve all the dates between a start and end date
    """

    data = auth2_client.time_series('activities/steps', base_date=start_date, end_date=end_date)
    dates_list = []

    for i in data['activities-steps']:
        dates_list.append(i['dateTime'])

    return dates_list


def get_weeks(auth2_client, start_date, end_date):
    """
    Retrieve the 7-day ranges (i.e. weeks) between a start date and end date, shifting the window 1 day at a time
    (e.g. [15/12/19 - 22/12/2019] ... [16/12/19- 23/12/19] ... [17/12/19 - 24/12/19] ...)
    """

    data = auth2_client.time_series('activities/steps', base_date=start_date, end_date=end_date)
    data_list = []
    current_week = []

    for i in data['activities-steps']:
        date_str = i['dateTime']        # date in format 2019-12-04
        current_week.append(datetime.datetime.strptime(date_str, '%Y-%m-%d'))    # convert the string representation of the date to a datetime object

        days_in_week = 7
        if (len(current_week) > days_in_week-1):
            day0 = current_week[0].strftime('%d %b %Y ')
            day6 = current_week[6].strftime('%d %b %Y ')
            data_list.append(day0 + " - " + day6)
            current_week.pop(0)

    return data_list


def get_daily_activity_data(activity_type, auth2_client, start_date, end_date):
    """
    Retrieve DAILY total aginast a specific dataset (e.g. steps/distance/floors/calories) between a start and end date
    """

    data = auth2_client.time_series('activities/' + activity_type, base_date=start_date, end_date=end_date)
    data_list = []

    for i in data['activities-' + activity_type]:
        print(activity_type, i['value'])
        if (activity_type != 'distance'):
            data_list.append(int(i['value']))
        else:
            data_list.append(float(i['value']) / 0.62137119)    # fitbit API doesn't allow us to choose km... so here I am manually converting miles -> km, jee wiz.

    return data_list


def get_weekly_activity_data(activity_type, auth2_client, start_date, end_date):
    """
    Retrieve WEEKLY total aginast a specific dataset (e.g. steps/distance/floors/calories) between a start and end date
    """

    data = auth2_client.time_series('activities/' + activity_type, base_date=start_date, end_date=end_date)
    data_list = []
    current_week = []

    for i in data['activities-' + activity_type]:
        if (activity_type != 'distance'):
            current_week.append(int(i['value']))
        else:
            current_week.append(float(i['value']) / 0.62137119)    # fitbit API doesn't allow us to choose km... so here I am manually converting miles -> km, jee wiz.
        
        days_in_week = 7
        if (len(current_week) > days_in_week-1):
            data_list.append(sum(current_week))
            print(activity_type, sum(current_week))         
            current_week.pop(0)

    return data_list


def get_daily_data(auth2_client, start_date, end_date):
    """
    Get data from every day between a start and end date, putting it all inside a dataframe
    """

    days = get_dates(auth2_client, start_date, end_date)
    daily_steps = get_daily_activity_data('steps', auth2_client, start_date, end_date)
    daily_distance = get_daily_activity_data('distance', auth2_client, start_date, end_date)
    daily_floors = get_daily_activity_data('floors', auth2_client, start_date, end_date)
    daily_calories = get_daily_activity_data('calories', auth2_client, start_date, end_date)

    daily_data_df = pd.DataFrame({
        'Date' : days,
        'Steps' : daily_steps,
        'Distance' : daily_distance,
        'Floors' : daily_floors,
        'Calories' : daily_calories
    })

    print('Dataframe populated with daily data')
    return daily_data_df


def get_weekly_data(auth2_client, start_date, end_date):
    """
    Get data from every week between a start and end date, putting it all inside a dataframe
    """

    weeks = get_weeks(auth2_client, start_date, end_date)
    weekly_steps = get_weekly_activity_data('steps', auth2_client, start_date, end_date)

    weekly_data_df = pd.DataFrame( {
        'Weeks' : weeks,
        'Steps' : weekly_steps
    })

    print('Dataframe populated with weekly data')
    return weekly_data_df


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


def get_persons_weekly_data(date_i_got_my_fitbit, client_id, client_secret):
    """
    Get someones weekly summation data.
    """

    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret
    server = Oauth2.OAuth2Server(CLIENT_ID, CLIENT_SECRET)
    server.browser_authorize()
    ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
    auth2_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)

    filename_weeklydata = 'weekly-data.csv'
    filename_almostfulldata = 'almost-full-data.csv'
    filename_fulldata = 'full-data.csv'

    start_date = date_i_got_my_fitbit
    end_date = datetime.date(2019, 12, 8)

    # get weekly summation data as a dataframe
    weekly_data_df = get_weekly_data(auth2_client, start_date, end_date)

    # invert the orientation of the dataframe, so that it is no longer vertical, but now it is displayed horizontally (left -> right)
    weekly_data_transposed = weekly_data_df.transpose()

    # put the dataframe in a csv file
    export_dataframe_to_csv(filename_weeklydata, weekly_data_transposed)

    # get the users name and profile picture and write to csv
    user_data = auth2_client.user_profile_get()
    user_data_df = pd.DataFrame({
        'Name' : [user_data['user']['displayName']],
        'Image URL' : [user_data['user']['avatar']]
    })

    # merge user data with weekly data
    exportedcsv_df = pd.read_csv(filename_weeklydata)
    print(user_data_df)
    print(exportedcsv_df)

    final_df = user_data_df.merge(exportedcsv_df, left_index=True, right_index=True)
    final_df.to_csv(filename_almostfulldata)

    # for some reason merging the 2 dataframaes together also added a new empty column at index=0... let's remove it!
    with open(filename_almostfulldata, 'r') as file_in:
        with open(filename_fulldata, 'w', newline='') as file_out:
            writer = csv.writer(file_out)
            for row in csv.reader(file_in):
                writer.writerow(row[1:])


def get_persons_daily_data(start_date, end_date, client_id, client_secret):
    """
    Get someone's daily data between two specified dates.
    Exports data to csv file.
    """

    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret
    server = Oauth2.OAuth2Server(CLIENT_ID, CLIENT_SECRET)
    server.browser_authorize()
    ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
    auth2_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)

    filename_dailydata = 'exports/daily-data.csv'

    daily_data_df = get_daily_data(auth2_client, start_date, end_date)
    export_dataframe_to_csv(filename_dailydata, daily_data_df)


#get_persons_weekly_data(datetime.date(2017, 6, 14), client_id='22B9W5', client_secret='7eab3ffe04c07a91f3cbda213a3c0433')
#get_persons_weekly_data(datetime.date(2017, 7, 4), client_id='22B9VL', client_secret='899aeed7920e3fbb1b77dd5a0449660a')

get_persons_daily_data(
    start_date=datetime.date(year=2020, month=3, day=28),
    end_date=datetime.date(year=2020, month=4, day=2),
    client_id='22B9W5',
    client_secret='7eab3ffe04c07a91f3cbda213a3c0433'
)


'''
https://app.flourish.studio/visualisation/1065441/edit
https://towardsdatascience.com/collect-your-own-fitbit-data-with-python-ff145fa10873
https://thispointer.com/python-how-to-convert-datetime-object-to-string-using-datetime-strftime/
https://www.journaldev.com/23365/python-string-to-datetime-strptime
'''
