import fitbit
import fitbit.gather_keys_ouath2 as Oauth2
import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import csv
import datetime
import time
import os
from openpyxl import load_workbook
from pandas import ExcelWriter

# some dates to experiment with...
yesterday = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))
yesterday2 = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
today = str(datetime.datetime.now().strftime("%Y%m%d"))
date_i_got_my_fitbit = datetime.date(2017, 6, 21)

path_to_exports_folder = 'fitbit-app/exports/'

class FitbitDataExtractor():

    def __init__(self, start_date, end_date):
        self.server = None
        self.auth2_client = None
        self.start_date = start_date
        self.end_date = end_date
    

    # setup server and initialise client request to fitbit API
    def setup(self, client_id, client_secret):
        CLIENT_ID = client_id
        CLIENT_SECRET = client_secret
        self.server = Oauth2.OAuth2Server(CLIENT_ID, CLIENT_SECRET)
        self.server.browser_authorize()
        ACCESS_TOKEN = str(self.server.fitbit.client.session.token['access_token'])
        REFRESH_TOKEN = str(self.server.fitbit.client.session.token['refresh_token'])
        self.auth2_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)
    

    # returns a list of dates
    def get_dates(self):
        data = self.auth2_client.time_series('activities/steps', base_date=self.start_date, end_date=self.end_date)
        dates_list = []

        for i in data['activities-steps']:
            dates_list.append(i['dateTime'])

        return dates_list
    

    # returns a list of each incremental week (i.e. 7-day range) by shifting the window 1 day at a time (e.g. [15/12/19 - 22/12/2019] ... [16/12/19- 23/12/19] ... [17/12/19 - 24/12/19] ...)
    def get_weeks(self):
        data = self.auth2_client.time_series('activities/steps', base_date=self.start_date, end_date=self.end_date)
        data_list = []
        current_week = []

        for i in data['activities-steps']:
            date_str = i['dateTime']        # date_str is in format (YYYY-MM-DD)
            current_week.append(datetime.datetime.strptime(date_str, '%Y-%m-%d'))    # convert the string representation of the date to a datetime object

            days_in_week = 7
            if (len(current_week) > days_in_week-1):
                day0 = current_week[0].strftime('%d %b %Y ')
                day6 = current_week[6].strftime('%d %b %Y ')
                data_list.append(day0 + " - " + day6)
                current_week.pop(0)
        
        return data_list


    # returns a list of each DAILY total aginast a specified dataset (e.g. steps/distance/floors/calories)
    def get_daily_activity_data(self, activity_type):
        data = self.auth2_client.time_series('activities/' + activity_type, base_date=self.start_date, end_date=self.end_date)
        data_list = []

        for i in data['activities-' + activity_type]:
            print(activity_type, i['value'])
            if (activity_type != 'distance'):
                data_list.append(int(i['value']))
            else:
                data_list.append(float(i['value']) / 0.62137119)    # fitbit API doesn't allow us to choose km... so here I am manually converting miles -> km, jee wiz.

        return data_list
    

    # returns a list of each DAILY total, but cascaded so the total keeps getting added to itself (i.e. alltime summation data) against a specified dataset (e.g. steps/distance/floors/calories)
    def get_cascaded_daily_activity_data(self, activity_type):
        data = self.auth2_client.time_series('activities/' + activity_type, base_date=self.start_date, end_date=self.end_date)
        data_list = []
        previous = 0

        for i in data['activities-' + activity_type]:            
            if (activity_type != 'distance'):
                data_list.append(int(i['value']) + previous)
            else:
                data_list.append((float(i['value']) + previous) / 0.62137119)    # fitbit API doesn't allow us to choose km... so here I am manually converting miles -> km, jee wiz.
            previous = data_list[-1]

        return data_list


    # returns a list of each WEEKLY total aginast a specified dataset (e.g. steps/distance/floors/calories)
    def get_weekly_activity_data(self, activity_type):
        data = self.auth2_client.time_series('activities/' + activity_type, base_date=self.start_date, end_date=self.end_date)
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


    # returns a dataframe containing all activity data (per day).
    def get_daily_data(self):
        days = self.get_dates()
        daily_steps = self.get_daily_activity_data('steps')
        daily_distance = self.get_daily_activity_data('distance')
        daily_floors = self.get_daily_activity_data('floors')
        daily_calories = self.get_daily_activity_data('calories')

        daily_data_df = pd.DataFrame({
            'Date' : days,
            'Steps' : daily_steps,
            'Distance' : daily_distance,
            'Floors' : daily_floors,
            'Calories' : daily_calories
        })

        print('Dataframe populated with daily data')
        return daily_data_df


    # returns a dataframe containing all cascaded activity data (per day)
    def get_cascaded_daily_data(self):
        days = self.get_dates()
        daily_steps = self.get_cascaded_daily_activity_data('steps')
        daily_distance = self.get_cascaded_daily_activity_data('distance')
        daily_floors = self.get_cascaded_daily_activity_data('floors')
        daily_calories = self.get_cascaded_daily_activity_data('calories')

        daily_data_df = pd.DataFrame({
            'Date' : days,
            'Steps' : daily_steps,
            'Distance' : daily_distance,
            'Floors' : daily_floors,
            'Calories' : daily_calories
        })

        print('Dataframe populated with daily data')
        return daily_data_df


    # returns a dataframe containing steps data (per incremental week).
    def get_weekly_data(self):
        weeks = self.get_weeks()
        weekly_steps = self.get_weekly_activity_data('steps')

        weekly_data_df = pd.DataFrame({
            'Weeks' : weeks,
            'Steps' : weekly_steps
        })

        print('Dataframe populated with weekly data')
        return weekly_data_df


    # get incremental weekly data, extract it into a csv file
    def extract_weekly_data(self, filename):
        fullpath_weeklydata = path_to_exports_folder + 'weekly-data.csv'
        fullpath_almostworkingdata = path_to_exports_folder + 'almost-working-data.csv'
        fullpath_flourishstudio = path_to_exports_folder + filename

        weekly_data_df = self.get_weekly_data()          # get weekly summation data as a dataframe        
        weekly_data_transposed = weekly_data_df.transpose()     # invert the orientation of the dataframe, so that it is no longer vertical, but now it is displayed horizontally (left -> right)        
        self.write_to_new_csv(fullpath_weeklydata, weekly_data_transposed)       # put the dataframe in a csv file

        # get the users name and profile picture and write to csv
        user_data = self.auth2_client.user_profile_get()
        user_data_df = pd.DataFrame({
            'Name' : [user_data['user']['displayName']],
            'Image URL' : [user_data['user']['avatar']]
        })

        # merge user data with weekly data
        exportedcsv_df = pd.read_csv(fullpath_weeklydata)
        print(user_data_df)
        print(exportedcsv_df)

        final_df = user_data_df.merge(exportedcsv_df, left_index=True, right_index=True)
        final_df.to_csv(fullpath_almostworkingdata)

        # for some reason merging the 2 dataframaes together also added a new empty column at index=0... let's remove it!
        with open(fullpath_almostworkingdata, 'r') as file_in:
            with open(fullpath_flourishstudio, 'w', newline='') as file_out:
                writer = csv.writer(file_out)
                for row in csv.reader(file_in):
                    writer.writerow(row[1:])

        # remove the 'almost-working-data.csv' file
        os.remove(fullpath_almostworkingdata)


    # write dataframe to a new csv file
    def write_to_new_csv(self, filename, df):
        # remove old file if it exists
        if (os.path.isfile(filename)):
            print('removing file... ', filename)
            os.remove(filename)
        
        fullpath = path_to_exports_folder + filename

        with open(fullpath, 'w', newline='') as f:
            df.to_csv(fullpath, mode='w', index=False, header=False)
        

    # Append dataframe to an existing csv file
    def append_to_existing_csv(self, filename, df):
        with open(filename, 'a', newline='') as f:
            df.to_csv(filename, mode='a', index=False, header=False)


    # add a new row to a csv file
    def add_new_row_to_csv(self, fullpath, new_row):
        with open(fullpath, 'a+', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(new_row)



# initialise user
user = FitbitDataExtractor(
    start_date=datetime.date(2020, 2, 13),
    end_date=datetime.datetime.now()
)

# setup user as client
user.setup(
    client_id='22BQQP',
    client_secret='66174409ee88d487787f255a08a9cd2b'
)

# get daily data, put into csv
user.write_to_new_csv('daily-data.csv', user.get_daily_data())

# get cascaded daily data, put into csv
#user.write_to_new_csv('cascaded-daily-data.csv', user.get_cascaded_daily_data())

# get weekly data, put into csv
#user.extract_weekly_data('flourish-studio.csv')
