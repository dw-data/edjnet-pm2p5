'''This script downloads the data from the CAMS europe reanalysis dataset
for the interval 2018 – 2022. It downloads one zip file for each month in the interval.
'''

import calendar
import cdsapi
from datetime import date
from dateutil.relativedelta import relativedelta
from os.path import isfile
import time as t
import urllib3
urllib3.disable_warnings()

def main():

    # Credentials for acessing the ADS api
    credentials = {

        "url": "https://ads.atmosphere.copernicus.eu/api/v2",
        "key": "YOUR API KEY"

    }

    # Starting one API session
    c = cdsapi.Client(url=credentials['url'], key=credentials['key'])


    # For each year, downloads data for every month
    for year in [ 2018, 2019, 2020, 2021, 2022 ]:
        for month in range(1, 13):
            month_str = f"{month:02d}"  # convert to two-digit string format

            # Creates a file name
            outpath = f'../data/CAMS-europe-reanalysis/raw/reanalysis/{year}-{month_str}.zip'

            # If there is already a file with this name (that is, the file was alraedy downloaded, skip this.)
            if isfile(outpath):
                continue

            # Save to a unique file per month
            c.retrieve(
                'cams-europe-air-quality-reanalyses',
                {
                    'variable': 'particulate_matter_2.5um',
                    'model': 'ensemble',
                    'level': '0',
                    'type': [
                        'interim_reanalysis', 'validated_reanalysis', # When available, get the validated analysis
                    ],
                    'year': [
                        year
                    ],
                    'month': month_str,
                    'format': 'zip',
                },
                outpath) 


if __name__ == "__main__":
    main()