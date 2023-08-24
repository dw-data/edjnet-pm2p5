'''
In this notebook, we will concatenate all the disparate CSV
files into useful, meaningful Excel files.
'''

import pandas as pd

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



###################################
### Yearly population estimates ###
###################################
def nuts0_yearly_patterns(inpath, outpath):

    df = pd.read_csv(inpath)

    # Removes columns we don't need
    df = df.drop(columns='region_code')
    
    df['time'] = pd.to_datetime(df.time)
    df['time'] = df.time.dt.year
    
    columns = {
        "time": "Year",
        "NUTS_ID": "NUTS ID",
        "CNTR_CODE": "Country code",
        "NAME_LATN": "Name (latin characters)",
        "pm2p5_mean": "Yearly PM 2.5 average (µg/m³)",
        "total_population": "Population estimate (GHSL 2020)",
        "affected_population_0-5": "0–5µg/m³ - population",
        "affected_population_5-10": "5–10µg/m³ - population",
        "affected_population_10-15": "10–15µg/m³ - population",
        "affected_population_15-20": "15–20µg/m³ - population",
        "affected_population_20-25": "20–25µg/m³ - population",
        "affected_population_25+": "25+ µg/m³ - population",
        "percentage_0-5": "0–5µg/m³ - percentage",
        "percentage_5-10": "5–10µg/m³ - percentage",
        "percentage_10-15": "10–15µg/m³ - percentage",
        "percentage_15-20": "15–20µg/m³ - percentage",
        "percentage_20-25": "20–25µg/m³ - percentage",
        "percentage_25+": "25+ µg/m³ - percentage",
    }

    # Renames columns for better reading
    df = df.rename(columns=columns)
    
    df = df[columns.values()]
    
    df.to_excel(outpath)


########################################
### NUTS3 level population estimates ###
########################################
def nuts3_yearly_patterns(inpath, outpath):

    df = pd.read_csv(inpath)

    # Removes columns we don't need
    df = df.drop(columns='region_code')
    
    df['time'] = pd.to_datetime(df.time)
    df['time'] = df.time.dt.year
    
    columns = {
        "time": "Year",
        "NUTS_ID": "NUTS ID",
        "CNTR_CODE": "Country code",
        "NAME_LATN": "Name (latin characters)",
        "pm2p5_mean": "Yearly PM 2.5 average (µg/m³)",
        "total_population": "Population estimate (GHSL 2020)",
        "affected_population_0-5": "0–5µg/m³ - population",
        "affected_population_5-10": "5–10µg/m³ - population",
        "affected_population_10-15": "10–15µg/m³ - population",
        "affected_population_15-20": "15–20µg/m³ - population",
        "affected_population_20-25": "20–25µg/m³ - population",
        "affected_population_25+": "25+ µg/m³ - population",
        "percentage_0-5": "0–5µg/m³ - percentage",
        "percentage_5-10": "5–10µg/m³ - percentage",
        "percentage_10-15": "10–15µg/m³ - percentage",
        "percentage_15-20": "15–20µg/m³ - percentage",
        "percentage_20-25": "20–25µg/m³ - percentage",
        "percentage_25+": "25+ µg/m³ - percentage",
    }

    # Renames columns for better reading
    df = df.rename(columns=columns)
    
    df = df[columns.values()]
    
    df.to_excel(outpath)

######################
### Daily datasets ###
######################
def nuts3_dw_patterns(inpath, outpath):


    df = pd.read_csv(inpath)
    
    if 'EU_category' not in df.columns:
        df = bin_pollution(df)
        
    
    columns = {
        "time": "Day",
        "NUTS_ID": "NUTS ID",
        "CNTR_CODE": "Country code",
        "NAME_LATN": "Name (latin characters)",
        "pm2p5_mean": "Daily PM 2.5 average (µg/m³)",
        "EU_category": "EU Air Quality Guidelines classification"
    }
    
    df = df.rename(columns=columns)
    
    df = df[columns.values()]
    
    if df.shape[0] < 2739000:
        df.to_excel(outpath)
    else:
        df.to_csv(outpath)
    
  

def main():

    # nuts0_yearly_patterns("../output/csvs/reanalysis-NUTS0-Y.csv", "../output/excel/CAMS-Europe-Renalaysis-Countries-Yearly-2018-2022.xlsx")
    # nuts0_yearly_patterns("../output/csvs/forecast-classified-NUTS0-Y-2022.csv", "../output/excel/CAMS-Europe-Forecast-Countries-Yearly-2022.xlsx")
    # nuts3_yearly_patterns("../output/csvs/reanalysis-NUTS3-Y.csv", "../output/excel/NUTS3-population-estimates-2018-2022-CAMS-reanalysis.xlsx")

    # nuts3_dw_patterns("../output/csvs/forecast-classified-NUTS3-1D-2023.csv", "../output/excel/CAMS-Europe-Forecast-Daily-2023.xlsx")
    # nuts3_dw_patterns("../output/csvs/forecast-classified-NUTS3-1D-2022.csv", "../output/excel/CAMS-Europe-Forecast-Daily-2022.xlsx")
    
    nuts3_dw_patterns("../output/csvs/reanalysis-NUTS3-Y.csv", "../output/excel/CAMS-Europe-Renalysis-Yearly-2018-2022.xlsx")
    # nuts3_dw_patterns("../output/csvs/reanalysis-NUTS3-W.csv", "../output/excel/CAMS-Europe-Renalysis-Weekly-2018-2022.xlsx")
    nuts3_dw_patterns("../output/csvs/forecast-classified-NUTS3-W-2023.csv", "../output/excel/CAMS-Europe-Forecast-Weekly-2023.xlsx")


if __name__ == "__main__":
    main()
