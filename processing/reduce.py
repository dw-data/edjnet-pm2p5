'''
This file will take the .nc files, read it using xarray and reduce
them in order to have a datapoint for each day instead of using
all the hourly intervals.
'''

import glob
import pandas as pd
import rioxarray as rxr
import xarray as xr

def get_files(pattern):
    '''
    Finds all files that match the specified
    glob string pattern.
    '''
    
    return glob.glob(pattern)


def concatenate(ds_list):
    '''
    Concatenates all the downloaded .netcdf files,
    which are speciefied if the filenames array.
    '''

    return xr.concat(ds_list, dim='time').sortby('time')


def resample(ds):
    '''
    Resamples the dataset data, creating one data variable
    for the mean, maximum and minimum pollution concentrations
    observed in each day.
    '''
    
    # orders the time so we can apply the daily average
    ds = ds.sortby('time')

    # uses resample to get the daily mean
    mean = ds.resample(time='1D').mean()
    
    # Create a new dataset for resampled data
    ds_resampled = xr.Dataset()

    for var in ds.data_vars:
        ds_resampled[var+'_mean'] = mean[var]

    return ds_resampled


def set_crs(ds):
    '''
    Sets a CRS for the naive raster file
    '''
    return ds.rio.write_crs("epsg:4326")



def main():

    for data_type in ['europe-reanalysis', 'europe-forecast']:


        if data_type == 'europe-reanalysis':
            path = f"../data/CAMS-{data_type}/unzipped/reanalysis/"
        elif data_type == 'europe-forecast':
            path = f"../data/CAMS-{data_type}/raw/forecast/"
        

        ### Some years have a slightly different grid cell which prevents proper concatenation
        ### that we will have to take care of later (on 6.reproject.py)
        for year in ["2018", "2019", "2020", "2021", "2022", "2023"]:

            filenames = get_files(f"{path}/{year}-*.nc")
            filenames = sorted(filenames)

            ds_list = []
            for filename in filenames:

                print("opening", filename)
                ds = xr.open_dataset(filename)

                print("resampling", filename)
                ds = resample(ds)
            
                print("setting crs", filename)
                ds = set_crs(ds)


                # Takes the opportunity to fix the time of the forecast data, which is in
                # NANOSECONDS SINCE THE START DATE. Also renames columns and squeeze
                if data_type == 'europe-forecast':


                    # Renames columns
                    print("renaming")
                    ds = ds.rename({"pm2p5_conc_mean": "pm2p5_mean"})

                    # Squeezes on level
                    print("squeezing")
                    ds = ds.squeeze()

                    print("Fixing time...")
                    start_date = pd.Timestamp(f'{year}-01-01 00:00:00')
                    ds['time'] = start_date + pd.to_timedelta(ds['time'].values, unit='ns')

                print("appending", filename)
                ds_list.append(ds)


            if len(ds_list) == 0:
                continue

            print("Concatenating...")
            ds = concatenate(ds_list)

            # Standardizes column names
            print("Renaming...")
            if data_type == 'europe-reanalysis':
                print("lon lat to x y")
                corresp = {'lon': 'x', 'lat': 'y'}

            elif data_type == 'europe-forecast':
                print("longitude latitude to x y")
                corresp = {'longitude': 'x', 'latitude': 'y' }

            ds = ds.rename(corresp)

            if data_type == 'europe-forecast':
                print("Converting longitudes...")
                # Converts lon from 0 to 360 to -180 to 180
                ds = ds.assign_coords(x=(((ds.x + 180) % 360) - 180))

            print(ds.coords)


            print("saving")
            ds.to_netcdf(f"../output/4.{data_type}-reduced-{year}.netcdf")

    

if __name__ == "__main__":
    main()