'''
This scripts generates CSV files with the population estimtates
of people living with high pollution levels in different
countries and NUTS regions at differente time intervals, 
as well as pm2p5 averages throughout the area.
'''

from functools import reduce
from geocube.api.core import make_geocube
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from os.path import isfile
import pandas as pd
from rasterio.enums import Resampling
import rioxarray
import xarray as xr
import time
import warnings

##################
#### SETTINGS ####
##################

pd.options.mode.chained_assignment = None  # default='warn'
warnings.simplefilter(action='ignore', category=FutureWarning)

#################
#### HELPERS ####
#################

def rescale(raster, factor, algorithm):
    """
    Rescales the resolution of a rio xarray dataset based on a specified scaling factor and resampling algorithm.

    Parameters
    ----------
        raster (xarray.Dataset): The input raster dataset whose resolution is to be rescaled.
        factor (float): The scaling factor used for rescaling. A value less than 1 decreases the resolution 
                        of the raster, yielding fewer pixels and thus larger individual pixels. A value greater 
                        than 1 increases the resolution, resulting in a larger number of smaller pixels. 
                        For example, a factor of 2 will double the raster's resolution, while a factor of 0.5 
                        will halve it.
        algorithm (rasterio.enums.Resampling): The resampling algorithm to be used during the rescaling operation. 
                                               Choices include methods like 'bilinear', 'cubic', 'nearest', etc.

    Returns
    -------
       xarray.Dataset: The rescaled raster image with altered resolution.
       

    Notes
    -----
    This docstring was created with the help of GPT-4, an AI language model developed by OpenAI.
    """

    new_width = int(raster.rio.width * factor)
    new_height = int(raster.rio.height * factor)

    raster = raster.rio.reproject(
        raster.rio.crs,
        shape=(new_height, new_width),
        resampling=algorithm,
    )


    return raster



def get_zones(raster, vector, varname, keyname='region_code'):
    """
    Attributes each grid cell of a raster to a unique ID based on intersection with vector polygons. The function 
    allows to optionally include time as a coordinate and also returns a correspondence dictionary for easier access.
    
    Parameters
    ----------
    raster : xr.DataArray
        The input raster data. 
    vector : gpd.GeoDataFrame
        The input vector data. It should be filtered and have the keyname column assigned.
    varname : str
        The name of the variable in the raster to use in the output grid – 
    keyname : str, optional
        A string representing the column values that will be added to the output grid, 
        marking to which polygon each pixel belongs. Defaults to 'region_code'.

    
    Returns
    -------
    outgrid : xr.Dataset
        The output grid with grid cells marked with unique IDs. If 'time' is True, time is also included as a coordinate.
    corresp : dict
        A correspondence dictionary mapping unique polygon IDs to the respective 'keyname' values for easy access.
        
    Notes
    -----
    This docstring was created with the help of GPT-4, an AI language model developed by OpenAI.
    """

    
    # Saves the for afterwards
    time_dim = raster.time
    
    # Keeps only the variable of interest
    raster = raster[varname]
        
    # Creates a key to mark the grid cells with
    vector[keyname] = range(0, vector.shape[0]) # in geocube, the ids need to be numbers :/
      
    # A correspondence dict for easier access
    corresp = {row["NUTS_ID"]: row[keyname] for index, row in vector[[keyname, 'NUTS_ID']].iterrows()}
    
    # Creates an output grid – that is, an xarray representation of the vector data
    # but with no values associated
    outgrid = make_geocube(
        vector_data=vector, # The shapes that we will use as a mold
        measurements=[keyname], # This is the LABEL we will stamp the pixels with
        like=raster, # The new cube will have the shape of the raster
    )
    
    return outgrid, corresp



def reproject_to_match(source, target):
    """
    Reprojects the source raster to match the target raster's shape, resolution, and coordinates.
    
    Parameters
    ----------
        source (xarray.DataArray): The input raster data to be reprojected.
        target (xarray.DataArray): The target raster data which the source raster will be matched to.
        
    Returns
    -------
        xarray.DataArray: The reprojected source raster that matches the target raster's shape, resolution, 
                          and coordinates.
                      
    Notes
    -----
    This docstring was created with the help of GPT-4, an AI language model developed by OpenAI.
    """
    # Reprojects the source raster to match the target raster
    rpjct = source.rio.reproject_match(target, resampling=Resampling.sum)

    # Assigns the coordinates from the target raster to the reprojected source raster to avoid rounding errors
    rpjct = rpjct.assign_coords({
        "x": target.x,
        "y": target.y, 
    })

    return rpjct


def get_masks(pm2p5, thresholds=[0, 5, 10, 15, 20, 25]):
    '''
    Generates a list of masks and corresponding labels for an input dataarray.
    
    Each mask corresponds to a range of values defined by the thresholds. For instance,
    the first mask will cover the range from thresholds[0] to thresholds[1], the second
    mask will cover the range from thresholds[1] to thresholds[2], and so on. The masks
    can be used to filter the dataarray for values within specific ranges.
    
    The last mask will cover the range from the last threshold to infinity.
    
    Parameters
    ----------
    pm2p5 : xarray.DataArray
        The input dataarray from which the masks are to be generated.
        This array should represent the pm2.5 concentration data.
    thresholds : list, optional
        The list of thresholds defining the ranges for which masks are to be generated.
        Default is [0, 5, 10, 15, 20, 25].
    
    Returns
    -------
    masks : list of xarray.DataArray
        The list of generated masks. Each mask corresponds to a range of values.
    labels : list of str
        The list of labels corresponding to each mask. Each label represents the
        range of values that the corresponding mask covers.
    
    Example
    -------
    masks, labels = get_masks(pm2p5)
    for mask, label in zip(masks, labels):
        print(f"For range {label}, there are {mask.sum()} cells.")
    '''
    
    # Initialize an empty list for the masks
    masks = []

    # Initialize an empty list for the labels
    labels = []

    # Iterate over the thresholds
    for i in range(len(thresholds) - 1):
        # Create a mask for each range
        mask = (pm2p5.pm2p5_mean >= thresholds[i]) & (pm2p5.pm2p5_mean < thresholds[i+1])

        # Append the mask to the list
        masks.append(mask)

        # Create a label for each range
        label = f"{thresholds[i]}-{thresholds[i+1]}"

        # Append the label to the list
        labels.append(label)

    # Create a mask for the last threshold ("25+")
    mask = (pm2p5.pm2p5_mean >= thresholds[-1])
    masks.append(mask)
    labels.append(f"{thresholds[-1]}+")
    
    return masks, labels


def compute_affected_population(ghsl, zones, masks, labels):
    """
    Computes the total affected population in each region for various ranges of pollution.
    
    This function uses a list of masks to filter the population data for specific ranges of 
    pollution. For each mask, the function calculates the sum of the population in areas where 
    the pollution level falls within the range that the mask represents. The function also 
    computes the total population per region without applying any masks. The function outputs 
    a dataframe where each column represents the total affected population for a specific range
    of pollution levels, along with a column for the total population per region.
    
    Parameters
    ----------
    ghsl : xarray.DataArray
        A data array representing the global human settlement layer (GHSL) population grid.
    zones : xarray.Dataset
        A dataset representing the different regions/zones.
    masks : list of xarray.DataArray
        A list of masks representing the different ranges of pollution. Each mask should 
        correspond to a range of pollution levels.
    labels : list of str
        A list of labels for each mask. Each label should represent the range of pollution 
        levels that the corresponding mask covers.
    
    Returns
    -------
    merged : pandas.DataFrame
        A dataframe where each column represents the total affected population for a specific 
        range of pollution levels, along with a column for the total population per region.
        The index of the dataframe represents the region codes.
    """

    # Re-assign the coordinates to match the zones
    ghsl = ghsl.assign_coords({"x": zones["x"], "y": zones["y"]})
    
    # Attributes a zone to each population grid
    ghsl['region_code'] = zones.region_code

    # Calculate the total population per region without applying any masks
    total_pop = ghsl.groupby("region_code").sum().population.to_dataframe().reset_index()
    total_pop = total_pop.rename(columns={"population": "total_population"})

    # Generate a list to store the dataframes
    dfs = [total_pop]

    # For each mask in the list
    for mask, label in zip(masks, labels):
        
        print(f"Processing mask: {label}")
        
        # Assign coordinates to mask
        mask = mask.assign_coords({"x": ghsl.x, "y": ghsl.y, "time": ghsl.time})
        
        # Applies the mask
        masked_ghsl = ghsl.where(mask)
        
        # The region code always should persist, even if the 
        # mask applies to it. The population values are the only ones
        # that should be filtered.
        masked_ghsl["region_code"] = ghsl.region_code
        
        print("attempting xarray groupby")
        # Apply the mask to the data
        affected_pop = (masked_ghsl
                            .groupby("region_code")
                            .sum()
                            .population)
        
        #display(affected_pop)
        print("attempting convertion to dataframe")
        affected_pop = (affected_pop.to_dataframe()
                                    .reset_index())
        
        #display(affected_pop)
                
        # Rename the column to reflect the range of values it represents
        affected_pop = affected_pop.rename(columns={"population":f"affected_population_{label}"})
        
        print("appending")
        # Append to the list of dataframes
        dfs.append(affected_pop)

    # Merge all dataframes
    merged = reduce(lambda left,right: pd.merge(left,right, on=['region_code', 'time'], how='left'), dfs)

    # Remove redundant columns
    merged = merged.drop(columns=[col for col in merged.columns if '_x' in col or '_y' in col])
    
    return merged


def compute_pollution_average(pm2p5, zones):
    """
    This function creates a DataFrame that summarizes the average pollution for each region. 

    Parameters
    ----------
    pm2p5 : xarray.DataArray
        An xarray DataArray object representing pollution distribution (specifically PM2.5).
        It is expected to have 'pm2p5_mean' as a data variable and 'x' and 'y' as coordinates.
        
    zones : xarray.DataArray
        An xarray DataArray object representing zones or regions.
        It is expected to have 'region_code' as a data variable and 'x' and 'y' as coordinates.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with each row representing a unique region (as identified by 'region_code'). 
        It has the following columns:
        - 'region_code': the unique identifier of each region.
        - 'pm2p5_mean': the average pollution (PM2.5) in the region.
    Notes
    -----
    This docstring was created with the help of GPT-4, an AI language model developed by OpenAI.
    """
    
    pm2p5 = pm2p5.assign_coords({"x": zones["x"], "y": zones["y"]})

    # Attributes a zone to each population grid
    pm2p5['region_code'] = zones.region_code
    
    # Creates a groupby over region and turns it into a dataframe
    avg_pollution = pm2p5.groupby("region_code")\
                        .mean()\
                        .pm2p5_mean\
                        .to_dataframe()\
                        .reset_index()

    # Renames columns to avoid merge issues
    avg_pollution = avg_pollution.rename(columns={"population":"total_population"})

    return avg_pollution

###################################
#### Main computation function ####
###################################

def compute(
         pm2p5_path, pm2p5_source, 
         ghsl_path,
         nuts_path, nuts_level,
         timegroup,
         rescale_factor,
         time_slice,
):

        
    # Output path
    csv_path = f"../output/csvs/reanalysis-NUTS{nuts_level}-{timegroup}.csv"
    if isfile(csv_path):
        print("File already present. Skipping.")
        return

    
    print("Reading data...")
    pm2p5 = xr.open_dataset(pm2p5_path, decode_coords='all')
    ghsl = xr.open_dataset(ghsl_path, decode_coords='all').squeeze()
    nuts = gpd.read_file(nuts_path)
    
    print("Filtering time...")
    #### Keeps only observations in the time slice
    pm2p5 = pm2p5.sel(time=slice(*time_slice))

    #### Adjust names to be descriptive if needed
    print("Adjusting variable names...")
    ghsl = ghsl.rename({"band_data":"population"})
  
    print("Filtering NUTS...")
    # Keep only the NUTS level of interest
    nuts = nuts[nuts.LEVL_CODE==nuts_level].reset_index()
    
    #### Compute yearly average for pm2p5, if needed
    print("Computing average...")
    pm2p5 = pm2p5.resample(time=timegroup).mean()
    
    #### Rescale the pm2p5 data to fit in NUTS units, if needed
    print("Rescaling...")
    pm2p5 = rescale(raster=pm2p5,
                    factor=rescale_factor,
                    algorithm=Resampling.nearest,
                    )
    
    #### Use the 'cookie cutter' to attribute a country value to pm2p5 grid
    print("Getting zones...")
    zones, corresp = get_zones(raster=pm2p5,
                      vector=nuts,
                      varname='pm2p5_mean',
                      keyname='region_code',
                     )
    
    #### Reproject the population data so it matches the rescaled pm2p5 data
    print("Reprojecting GHSL...")
    ghsl = reproject_to_match(source=ghsl, target=pm2p5)
    
    # GHSL needs a time dimensions similar to pm2p5
    steps = pm2p5.time.values
    ghsl = ghsl.expand_dims(time=steps)
    ghsl = ghsl.assign_coords({"x": pm2p5.x, "y":pm2p5.y, "time":pm2p5.time})
            
    #### For each pixel, determine whether it passes the threshold
    print("Making masks...")
    masks, labels = get_masks(pm2p5)
            
    #### Now we can use the thresholds, the population estimates and the zones
    #### to create our comparison
    print("Calculating population shares...")
    if timegroup != 'D':
        population_gdf = compute_affected_population(ghsl, zones, masks, labels)
    
    #### Creates an average yearly pollution dataframe
    print("Calculating pollution averages..")
    pollution_gdf = compute_pollution_average(pm2p5, zones)
        
    # Merges all of that with NUTS data
    print("Making final dataframe adjustments...")
    
    # Only yearly data should have population counts
    if timegroup != 'D':
        result = population_gdf.merge(pollution_gdf, on=['region_code', 'time'])
    else:
        result = pollution_gdf.copy()
    
    nuts['region_code'] = nuts['NUTS_ID'].map(corresp)
        
    # Adds nuts info
    result = nuts[["region_code", 
                 "NUTS_ID", "CNTR_CODE", 
                 "NAME_LATN", "geometry"]].merge(result, on=['region_code'])
    
    # Computes percentages
    if timegroup != 'D':
        for label in labels:
            result[f"percentage_{label}"] = result[f"affected_population_{label}"] / result["total_population"]

    # Rounds values
    for column in result.columns:
        if '_population' in column:
            result[column] = result[column].round()
            
        if 'percentage_' in column:
            result[column] = result[column]
            
        if 'mean' in column:
            result[column] = result[column]
    
          
    result = result.drop(columns=[col for col in result.columns if '_y' in col or '_x' in col or 'band' in col])
    result = result.fillna(0)
    
    print("Saving as csv")
    csv = result.drop(columns='geometry')
    csv.to_csv(csv_path, index=False)
    print()
    print("***")
               
    # return {
    #     "gdf": result,
    #     "pm2p5": pm2p5,
    #     "zones": zones,
    #     "ghsl": ghsl,
    #     "corresp": corresp,
    #     "threshold_masks": (masks, labels)
    # }


########################
#### MAIN EXECUTION ####
########################

def main():

    # Europe reanalysis
    for timegroup in ['Y', 'D', 'W']:
        for nuts_level in  [0, 1, 3]:
            print(f"Computing {timegroup} at NUTS level {nuts_level}")
            data = compute(
                time_slice=(f"2018-01-01", f"2022-12-31"),
                pm2p5_path = f"../output/5.europe-reanalysis-reprojected.netcdf",
                pm2p5_source = 'europe-renalysis',
                rescale_factor = 3,
                nuts_path = "../output/NUTS/expanded-NUTS.json",
                nuts_level = nuts_level,
                ghsl_path = "../output/5.ghsl-europe-reanalysis-reprojected.netcdf",
                timegroup=timegroup
            )
            print()


if __name__ == "__main__":
	main()
