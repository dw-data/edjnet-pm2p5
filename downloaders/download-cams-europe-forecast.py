'''This script downloads the data from the CAMS europe forecast dataset
for the interval 2022 – current data in 2023. It downloads it as one
single zip file for each year.
'''

import calendar
import cdsapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
import glob
from os import remove
from os.path import isfile
from secrets import CAMS_KEY
import time as t
import urllib3
urllib3.disable_warnings()

def main():

    credentials = {

        "url": "https://ads.atmosphere.copernicus.eu/api/v2",
        "key": CAMS_KEY

    }

    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])

    for year in ['2023', '2022']:

        # Gets all the data available for each year
        if year == '2022':
            start = '2022-01-01'
            limit = '2022-12-31'

        else:   
            start = '2023-01-01'
            limit = datetime.today().strftime("%Y-%m-%d")


        # Sets a file name
        outpath = f'../data/CAMS-europe-forecast/raw/forecast/{start}_{limit}.nc'

        # If there is already a file with this name (that is, the file was alraedy downloaded), skip it.
        if isfile(outpath) and (year != "2023"):
            continue

        # If we are downloading a new file for 2023, we need to remove the previously existing 2023 file.
        if year == "2023":
            files = glob.glob("../data/CAMS-europe-forecast/raw/forecast/2023*.nc")
            if len(files) > 0:
                remove(files[0])

        c.retrieve(
            'cams-europe-air-quality-forecasts',
            {
                'model': 'ensemble',
                'format': 'netcdf',
                'level': '0',
                'date': f'{start}/{limit}',
                'type': 'analysis',
                'variable': 'particulate_matter_2.5um',
                'time': [
                    '00:00', '01:00', '02:00',
                    '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00',
                    '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00',
                    '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00',
                ],
                'leadtime_hour': '0',
            },
            outpath)



if __name__ == "__main__":
    main()