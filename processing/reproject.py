'''
In this script, we will make sure that the datasets
download from CAMS are properly alligned and in the
same CRS. This is needed because of slight shape
varations in 2022 and 2020 that produce unexpected
results in the Europe Reanalysis dataset.
'''

from rasterio.enums import Resampling
import rioxarray as rxr
import xarray as xr


def reproject_and_assign_coords(ds_target, ds_list):
    """
    Reproject datasets in ds_list to match the spatial resolution and 
    coordinate system of ds_target.

    Parameters:
    - ds_target (xarray.Dataset): The target dataset to which the other datasets will be reprojected.
    - ds_list (list of xarray.Dataset): A list of datasets that need to be reprojected.

    Returns:
    - list of xarray.Dataset: A list of reprojected datasets with coordinates matched to ds_target.

    Note:
    - Assumes that the `rio` accessor (from `rioxarray`) is available for the datasets.
    """
    
    reprojected_datasets = []

    for ds in ds_list:
        
        ds_reprojected = ds.rio.reproject_match(ds_target)

        ds_reprojected = ds_reprojected.assign_coords({"x": ds_target.x, "y": ds_target.y})

        reprojected_datasets.append(ds_reprojected)       

    return reprojected_datasets




def main():


    for data_type in ['europe-reanalysis', 'europe-forecast']:


        # Each type of dataset covers a different time range
        if data_type == 'europe-reanalysis':
            years = ["2018", "2019", "2020", "2021", "2022"]

        elif data_type == 'europe-forecast':
            years = ["2022", "2023"]

        # Creates a dictionary with all the datasets
        datasets = { }
        for year in years:
            datasets[year] = xr.open_dataset(f"../output/4.{data_type}-reduced-{year}.netcdf", decode_coords='all')

        # 2022 as the target year, all others should be reprojected according to it
        target = datasets["2022"]
        to_reproject = [ datasets[year] for year in years if year != "2022"]

        # Reprojects
        reprojected_datasets = reproject_and_assign_coords(target, to_reproject)

        # Concatenates and saves the reprojected datasets
        reprojected_datasets.append(target)
        reprojected_datasets = xr.concat(reprojected_datasets, dim='time')
        reprojected_datasets.to_netcdf(f"../output/5.{data_type}-reprojected.netcdf")

        # Also reprojects the GHSL layer
        ghsl = xr.open_dataset("../data/GHSL/whole-globe/ghsl.tif")
        ghsl = ghsl.rio.reproject_match(reprojected_datasets, resampling=Resampling.sum)

        # Assigns the coordinates from the target raster to the reprojected source raster to avoid rounding errors
        ghsl = ghsl.assign_coords({
            "x": reprojected_datasets.x,
            "y": reprojected_datasets.y, 
        })

        ghsl.to_netcdf(f"../output/5.ghsl-{data_type}-reprojected.netcdf")


if __name__ == "__main__":
    main()
