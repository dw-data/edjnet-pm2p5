'''
This script includes subdivisions for
Ukraine, Kosovo, Moldova and Bosnia Herzegovina
in the regular NUTS 2021 geojson.
'''

import geopandas as gpd
import pandas as pd

def standardize_columns(geometries, assigned_level):
        
    geometries['NUTS_ID'] = geometries['id']
    geometries['LEVL_CODE'] = assigned_level
    geometries['CNTR_CODE'] = geometries['NUTS_ID'].str[:3]
    geometries['NAME_LATN'] = geometries['name']
    geometries['NUTS_NAME'] = geometries['name']
    
    geometries = geometries.drop(columns=["name"])
    
    return geometries


def main():
    
    # Original nuts file
    nuts = gpd.read_file("../data/NUTS/nuts-2021.geojson")

    ### We will treat the always treat the smallest division available as level 3,

    # Ukraine has divisions equivalent to NUTS 0, 2 and 3
    ukr_0 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Ukraine/UKR_N0.geojson")
    ukr_3 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Ukraine/UKR_N3.geojson")
    
    # Fixes unknown ukraine division
    ukr_3.id = ukr_3.id.str.replace("?", "UKR.xxx", regex=False)
    ukr_3.name = ukr_3.name.str.replace("?", "Unknown name Ukraine division")

    # Kosovo has divisions equivalent to NUTS 0, 2
    kos_0 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Kosovo/XKO_N0.geojson")
    kos_3 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Kosovo/XKO_N2.geojson")

    # Bosnia and Herzegovina has divisions equivalent to nuts 0, 2 and 3
    bos_0 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Bosnia/BIH_N0.geojson")
    bos_3 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Bosnia/BIH_N3.geojson")

    # Moldova has divisions equivalent to NUTS 0 and 2
    mol_0 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Moldova/MDA_N0.geojson")
    mol_3 = gpd.read_file("../data/NUTS/geometries_BIH_XKO_MDA_UKR/Moldova/MDA_N2.geojson")

    level_0 = [ukr_0, kos_0, bos_0, mol_0]
    level_3 = [ukr_3, kos_3, bos_3, mol_3]
    
    ### Now we will standardize column names
    for geometries in level_0:
        geometries = standardize_columns(geometries, 0)
    for geometries in level_3:
        geometries = standardize_columns(geometries, 3)  
        
   
    ### We will also remove the other levels from the general nuts file
    nuts = nuts[nuts.LEVL_CODE.isin([0, 1, 3])].reset_index(drop=True)
    
    ### And finally concatenate all
    nuts = pd.concat([nuts] + level_0 + level_3, ignore_index=True)
    
    nuts.to_file("../output/NUTS/expanded-NUTS.json", driver='GeoJSON')

if __name__ == "__main__":
    main()