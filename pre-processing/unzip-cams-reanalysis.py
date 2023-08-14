'''
This script simply unzips the reanalysis iles downloaded from the CAMS ADS.
Adapted from https://github.com/InfoAmazonia/engolindo-fumaca/blob/master/code/2_unzip_organize_cams_dataset.py
'''

import zipfile
import glob
import os

def main():

    wd = '../data/CAMS-europe-reanalysis/raw/reanalysis/'
    td = '../data/CAMS-europe-reanalysis/unzipped/reanalysis/'

    zip_files = glob.glob(f'{wd}*.zip')

    for zip_file in zip_files:

        zipdata = zipfile.ZipFile(zip_file)
        zipinfos = zipdata.infolist()

        for zipinfo in zipinfos:

            zipinfo.filename = os.path.basename(zip_file).replace('.zip', '.nc')
            zipdata.extract(zipinfo, td)


if __name__ == "__main__":
    main()