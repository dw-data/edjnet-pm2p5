'''
This script is used to process the slightly different
data format used in the CAMS Forecast data.
'''

from functools import reduce
from geocube.api.core import make_geocube
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from rasterio.enums import Resampling
import rioxarray
import xarray as xr
import warnings

import time
from contextlib import contextmanager

pd.options.mode.chained_assignment = None  # default='warn'
warnings.simplefilter(action='ignore', category=FutureWarning)

@contextmanager
def timer(description: str = 'Time elapsed'):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f'{description}: {elapsed:.2f}s')


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


def bin_pollution(df):  
    """
    Categorizes pollution data into different bins according to the EU and WHO standards.
    
    The EU standards use the following categories:
    - Good (0-10)
    - Fair (10-20)
    - Moderate (20-25)
    - Poor (25-50)
    - Very poor (50-75)
    - Extremely poor (75-800)

    The WHO standards use the following categories:
    - AQG level (0-15)
    - Interim target 4 (15-25)
    - Interim target 3 (25-37.5)
    - Interim target 2 (37.5-50)
    - Interim target 1 (50-75)
    - Over interim targets (75+)
    
    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame containing the pollution data. Must include a column 'pm2p5_mean' with the pollution levels.

    Returns
    -------
    pandas.DataFrame
        The input DataFrame with two new columns 'EU category' and 'WHO category' containing the category labels.
        
    """
    
    # Define the thresholds
    bins = [0, 10, 20, 25, 50, 75, 800]
    labels = ['Good (0-10)', 
              'Fair (10-20)', 
              'Moderate (20-25)', 
              'Poor (25-50)', 
              'Very poor (50-75)', 
              'Extremely poor (75-800)']

    # Use pd.cut() to categorize values
    df['EU_category'] = pd.cut(df['pm2p5_mean'], bins=bins, labels=labels, include_lowest=True)

    # Repeats for WHO levels
    bins = [0, 15, 25, 37.5, 50, 75, 800]
    labels = ["AQG level (0-15)", "Interim target 4 (15-25)" , 
              "Interim target 3 (25-37.5)", "Interim target 2 (37.5-50)", 
              "Interim target 1 (50-75)", "Over interim targets (75+)"]
    df['WHO_category'] = pd.cut(df['pm2p5_mean'], bins=bins, labels=labels, include_lowest=True)
    
    return df


def compute(nuts_level, timestep, year):
    '''
    This will craete a dataframe with mean pollution levels
    for each region in a given day, as well as the classification
    according to WHO and EU air quality guidelines.
    '''
    
    print("Starting the script...")
    start_time = time.time()
    
    
    ######################
    #### Reading NUTS ####
    ######################
    
    print("Reading nuts file")
    with timer('Reading NUTS file took'):

        # Keep only the NUTS level of interest
        nuts = gpd.read_file("../output/NUTS/expanded-NUTS.json")
        nuts = nuts[nuts.LEVL_CODE==nuts_level].reset_index()

    ##################################
    #### Preparing pollution data ####
    ##################################
    
    print("Reading and processing pollution data")
    with timer("Reading and processing pollution data took"):
    
        pm2p5_path = "../output/5.europe-forecast-reprojected.netcdf"

        print("Reading...")
        pm2p5 = xr.open_dataset(pm2p5_path, decode_coords='all')

        # Keeps only the relevant year
        pm2p5 = pm2p5.sel(time=year)

        # Now let's resample it
        print("Resampling...")
        pm2p5 = pm2p5.resample(time=timestep).mean()

    
    print("Rescaling population data")
    with timer('Rescaling pollution data took'):
        #### Rescale the pm2p5 data to fit in NUTS units
        pm2p5 = rescale(raster=pm2p5,
                        factor=3,
                        algorithm=Resampling.nearest)

                   
    ###################################
    #### Preparing population data ####
    ###################################
    
    print("Preparing GHSL data")
    with timer("Prepring GHSL data took"):
    
        print("Opening...")
        # Get's the ghsl data
        ghsl = xr.open_dataset("../output/5.ghsl-europe-forecast-reprojected.netcdf", decode_coords='all')
        
        print("Reprojecting to match...")
        #### Reproject the population data so it matches the rescaled pm2p5 data
        ghsl = reproject_to_match(source=ghsl, target=pm2p5)

        print("Assigning coords...")
        # They are already in the same dimensions. We can simply assign coords.
        ghsl = ghsl.assign_coords({"x": pm2p5.x, "y": pm2p5.y})

        print("Renaming variables...")
        # Rename columns so it makes better sense
        ghsl = ghsl.rename({"band_data": "population"})

        # Saves pm2p5 to access pixel data
        # ghsl.to_netcdf(f"../output/8-ghsl-pm2p5-{year}.netcdf")

        print("Assigning a time dimension...")
        # GHSL needs a time dimensions similar to pm2p5    
        steps = pm2p5.time.values
        ghsl = ghsl.expand_dims(time=steps)
        ghsl = ghsl.assign_coords({"x": pm2p5.x, "y":pm2p5.y, "time":pm2p5.time})
        




    #######################
    #### Compute zones ####
    #######################
    
    print("Creating zones")
    with timer('Creating zones took'):
        zones, corresp = get_zones(raster=pm2p5,
                                  vector=nuts,
                                  varname='pm2p5_mean',
                                  keyname='region_code',
                                  )
    
    ########################
    #### Creating masks ####
    ########################
    
    print("Making masks")
    with timer("Making masks took"):
        # Masks are increasing steps of the WHO threshold
        masks, labels = get_masks(pm2p5)

    ##########################################
    #### Creates the population dataframe ####
    ##########################################
    
    if timestep == 'Y' and year == '2022':
        print("Calculating population shares")
        with timer('Calculating population shares took'):
            population_gdf = compute_affected_population(ghsl, zones, masks, labels)
    
    #########################################
    #### Creates the pollution dataframe ####
    #########################################
    
    print("Calculating pollution average")
    with timer('Calculating pollution average took'):
        pollution_gdf = compute_pollution_average(pm2p5, zones)
    
    ############################################
    #### Adds the classification thresholds ####
    ############################################
    
    if timestep == '1D':
        
        print("Calculating pollution bins")
        with timer('Calculating pollution bins took'):
            pollution_gdf = bin_pollution(pollution_gdf)
    
    ########################
    #### Adds NUTS info ####
    ########################
    
    nuts['region_code'] = nuts['NUTS_ID'].map(corresp)
    
    if timestep == 'Y' and year == '2022':
        result = population_gdf.merge(pollution_gdf, on=['region_code', 'time'])
        for label in labels:
            result[f"percentage_{label}"] = result[f"affected_population_{label}"] / result["total_population"]
            
    else:
        result = pollution_gdf.copy()
        
    # Adds nuts info
    result = nuts[["region_code", 
                 "NUTS_ID", "CNTR_CODE", 
                 "NAME_LATN", "geometry"]].merge(result, on=['region_code'])
    

    # Rounds values
    for column in result.columns:
        if '_population' in column:
            result[column] = result[column].round()
            
        if 'percentage_' in column:
            result[column] = result[column].fillna(0)
            result[column] = result[column].round(3)
            
        if 'mean' in column:
            result[column] = result[column].round(3)
    
          
    result = result.drop(columns=[col for col in result.columns if '_y' in col 
                                                                or '_x' in col 
                                                                or 'band' in col
                                                                or 'geometry' in col
                                                                or 'spatial_ref' in col])
    #result = result.fillna(0)
    
    return result


def main():

    # Compute the whole thing for 2023
    df_2023 = compute(nuts_level=3, year='2023', timestep='1D') # Daily data for 2023, level 3
    df_2023.to_csv(f"../output/csvs/forecast-classified-NUTS3-1D-2023.csv", index=False)


    # Level 3 yearly and daily data for 2022
    df_2022_3_y = compute(nuts_level=3, year='2022', timestep='Y')
    df_2022_3_y.to_csv(f"../output/csvs/forecast-classified-NUTS3-Y-2022.csv", index=False)

    df_2022_3_d = compute(nuts_level=3, year='2022', timestep='1D')
    df_2022_3_d.to_csv(f"../output/csvs/forecast-classified-NUTS3-1D-2022.csv", index=False)


    # Level 0 yearly data for 2022
    df_2022_0 = compute(nuts_level=0, year='2022', timestep='Y')
    df_2022_0.to_csv(f"../output/csvs/forecast-classified-NUTS0-Y-2022.csv", index=False)


if __name__ == "__main__":
    main()