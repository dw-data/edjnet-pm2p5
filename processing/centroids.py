import xarray as xr
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def sample_raster_values(raster, points):   
    """
    Extracts time series from raster for given points.
    Returns a concatenated DataFrame.
    """
    
    results = []

    for index, row in points.iterrows():

        x, y = row.longitude, row.latitude

        # Extract the time series for the given point – if there's no time dimension
        # this should also work, albeit not very efficiently
        time_series_at_point = raster.sel(x=x, y=y, method='nearest')
        
        # Convert to DataFrame, add id data
        df_at_point = time_series_at_point.to_dataframe().reset_index()
        df_at_point['lau_id'] = row.lau_id
        df_at_point['lau_name'] = row.lau_name
        df_at_point['country'] = row.country
        df_at_point['x'] = round(row.longitude, 4)
        df_at_point['y'] = round(row.latitude, 4)

        
        # append to results
        results.append(df_at_point)

    # Concatenate
    results = pd.concat(results)
    return results


def simplify_csv(df):
    """
    Drops specified columns from DataFrame.
    Returns updated DataFrame.
    """
    df = df.drop(columns=[col for col in ['level', 'spatial_ref'] if col in df.columns])
    return df


def main():
    """
    Main function to read raster data, process daily and yearly values, and save as CSV.
    """

    # Reads raster data
    reanalysis = xr.open_dataset("../output/5.europe-reanalysis-reprojected.netcdf", decode_coords='all')
    forecast = xr.open_dataset("../output/5.europe-forecast-reprojected.netcdf", decode_coords='all')

    # Reads points
    points = pd.read_csv("../data/LAU_Centers/lau_2020_nuts_2021_pop_2018_p_2_adjusted_intersection.csv")
    points = points.groupby("country").apply(lambda x: x.nlargest(15, 'population')) # n largest cities of each country
    points = points.reset_index(drop=True)
    
    # 2022-2023 forecast daily values
    result = sample_raster_values(forecast, points)
    result = simplify_csv(result)
    result.to_csv("../output/csvs/centroids-forecast-1D.csv", index=False)
    
    # 2018-2022 daily values
    result = sample_raster_values(reanalysis, points)
    result = simplify_csv(result)
    result.to_csv("../output/csvs/centroids-reanalysis-1D.csv", index=False)

    # 2018-2022 yearly averages
    result = sample_raster_values(reanalysis.resample(time='Y').mean(), points)
    result = simplify_csv(result)
    result.to_csv("../output/csvs/centroids-reanalysis-Y.csv", index=False)

    
if __name__ == "__main__":
    main()