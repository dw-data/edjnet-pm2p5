GITHUB CONTENT

# Air Pollution in Europe

This repository contains the code and a brief methodological description of data analysis behind [this] piece, which was published by DW and the collaborators from the European Data Journalism Network.

—

## Methodology
The pollution figures on this story are the result of an DW Data analysis that used data provided by the Copernicus satellite system. Satellite pollution measurements are made using light sensors. The more polluted an area is, the less light is reflected from the ground back to the satellite. This difference, coupled with statistical modeling and other adjustments, allows scientists to estimate how polluted an area on Earth's surface is. 

This kind of data is specially useful for measuring pollution levels even in areas where air pollution sensors are few and far between. Such sensors are sparser in parts of the globe such as Africa and South America, but this is also the case in some areas of Europe as well. Nevertheless, this approach is considered less precise than using measurements made with on-the-ground sensors. 

Satellite observations also cram together extensive areas into a single observation: each measurement refers to a 10 square km area in the Earth's surface – also known as a satellite's "pixel size". In reality, the conditions on the ground would probably change within such a large territory. Moreover, more precise measurements are generally used in scientific research and when measuring results in order to enforce public policies.

The specific pollution data sources used for this project were the .netcdf raster files from the Copernicus' European air quality reanalysis dataset, with the exception of any 2023 figures, which come from the equivalent forecast data. 

In both cases, the original data showed hourly measurements at the surface level. The hourly data was first summarized into daily averages. The daily averages, on its turn, were averaged into yearly or weekly means, when necessary.

In order to estimate the population exposed to different thresholds of pollution, another satellite-based dataset was used: the Global Human Settlement Layer (GHSL), which estimates how many people live in each one of the satellite's pixels. 

Since the GHSL's pixel size (that is, the area covered by each data point) are significantly smaller than those in the pollution datasets, they had to be reprojected – that is, reshaped in order to match the latitudes, longitudes and pixel size of the Copernicus data. In practical terms, all the GHSL pixels that intercept a single Copernicus pixel had their population summed. As a result, each Copernicus pixel ended up with an estimate of the population that lived there.

It's important to highlight that GHSL estimates often don't match official census statistics. However, they come very close.

In order to estimate average pollution levels for each region or city, we used the European Union's NUTS statistical division. Each mentioned area is a level 3 NUTS unit – that is, the smallest available.. We selected all the pixels that were within the given unit and averaged them once again. 

A similar process was done to estimate the share of population exposed to each pollution threshold: we first selected all the pixels in a region that were above the said threshold and summed their population estimates.

For validating this data processing pipeline, the results were compared to data published by the European Environmental Agency in 2020. The overall trend was the same.

## Code structure
The source code available in this repository describes in detail how the process above was carried out.

The directory `downloaders` contains the scripts used to download data from the Copernicus API. Please notice that the data from the GHSL and NUTS shapefiles were downloaded manually and not using any scripts.

The directory `pre-processing` has all the scripts used to prepare the data for the processing described above, including unzipping the files and adding other regional divisions of interest to the NUTS shapefiles (namely regional divisions for European countries that are still not contemplated in the NUTS statistical division).

The directory `processing` contains the scripts that averaged and reprojected the satellite data and, ultimately, produced CSV files with estimated pollution and population estimates for each NUTS region in different time frames. Additionally, another script extracted pollution estimates for specific points (city centers), instead of averaging areas. Finally, the CSV files are also processed into easier-to-work-with Excel files.

Finally, the `viz` directory contains the scripts used to generate the maps shown in the piece, as well as another set of CSV files which powers the charts that were made with Datawrapper.


## Access to processed data

The files available in the output directory are the result of the process described above, with country and NUTS3-level estimates on pollution. 

The processed pixel-level data was too large to be published on GitHub, but if you are interested in them, please email data.team[at]dw.com. 
