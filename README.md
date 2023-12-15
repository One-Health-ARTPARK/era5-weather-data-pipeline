# ERA-5 and ERA-5 Land Data Extraction and Processing Pipeline

This Python script is designed to download, process, and aggregate [ERA-5]([url](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels)) and [ERA-5 Land]([url](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview)) reanalysis data for specific variables, years, months, and regions. The script interacts with the Climate Data Store (CDS) API, performs spatial processing using GeoJSON files, and allows users to aggregate the data temporally. The processed and aggregated data is saved in CSV format.

## Table of Contents

- [Overview](#overview)
- [Libraries Used](#libraries-used)
- [Script Structure](#script-structure)
  - [Import Statements](#import-statements)
  - [User Input Functions](#user-input-functions)
  - [Data Download Functions](#data-download-functions)
  - [Spatial Processing Functions](#spatial-processing-functions)
  - [Data Processing and Aggregation Functions](#data-processing-and-aggregation-functions)
  - [Main Execution](#main-execution)
- [Usage](#usage)
- [Important Notes](#important-notes)

## Overview

The provided Python script is designed to download, process, and aggregate ERA-5 and ERA-5 Land data for specific variables, years, months, and regions. The script interacts with the Climate Data Store (CDS) API, performs spatial processing using GeoJSON files, and allows users to aggregate the data on a weekly basis. The processed and/or aggregated data is saved in CSV format.

## Libraries Used

1. **cdsapi**: Used for accessing the CDS API and downloading reanalysis data.
2. **xarray**: Used for working with labeled multi-dimensional arrays (NetCDF files).
3. **pandas**: Used for data manipulation and CSV file operations.
4. **fuzzywuzzy**: Used for fuzzy string matching during user input.
5. **geopandas**: Used for working with geospatial data.
6. **shapely.geometry**: Used for creating geometric objects for spatial operations.

## Script Structure

### Import Statements

The script begins by importing necessary libraries and modules. 

### User Input Functions

1. **get_user_input(prompt, options=None):** A function to get user input, with optional predefined options.

2. **parse_month_input(month_input):** A function to parse user input for months, allowing for individual months or ranges.

### Data Download Functions

1. **download_era5_data(variable, year, month_input, times, region, dataset):** Downloads ERA-5 or ERA-5 Land data based on user input.

2. **extract_raw_data(netcdf_file, dataset):** Extracts raw data from the downloaded NetCDF file, converts it to a DataFrame, and saves it as a CSV file.

### Spatial Processing Functions

1. **coordinates_to_karnataka_hierarchy(df):** Maps coordinates to Karnataka's subdistrict and district hierarchy.

2. **coordinates_to_bbmp_hierarchy(df):** Maps coordinates to BBMP's ward hierarchy.

3. **get_geojsons(region_choice):** Returns the appropriate spatial processing function based on the region choice.

### Data Processing and Aggregation Functions

1. **process_data(df, variable, region_choice, dataset):** Processes spatial data and aggregates it based on quarters.

2. **perform_aggregation(combined_df, year, variable, region_choice, dataset):** Allows users to perform temporal aggregation and saves the processed data.

### Main Execution

The script's main execution follows these steps:

1. **User Input:** Asks users to choose the dataset, variable, year, months, frequency, and region.

2. **Data Download:** Downloads reanalysis data based on user input.

3. **Data Extraction:** Converts NetCDF data to CSV format.

4. **Spatial Processing and Aggregation:** Processes spatial data and aggregates it based on quarters.

5. **Data Saving:** Saves the processed and/or aggregated data in CSV format.

## Usage

1. Clone the repository.
2. Install dependencies.
3. Create a nano script with respective CDSAPI credentials in your home directory.
4. Run the script: python weather_data_pipeline.py

## Important Notes

1. Modify the config.py file as per requirements.
2. Aggregation is possible for a total of 230 subdistricts for Karnataka and 6 zones for BBMP.
3. All weather variables are in the same unit as specified by ERA. No modifications has been done with respect to this.
4. Note that the complete process - downloading, extraction, processing and aggregation for a single weather variable of a single year will take approximately 25-35 minutes. Kindly, check and re-run the script if it is taking more time than mentioned.
