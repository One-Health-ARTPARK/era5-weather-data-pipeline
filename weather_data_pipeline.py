import cdsapi
import xarray as xr
from config import available_era5_variables, available_era5_land_variables, available_months, available_times_hourly, available_times_4times, available_days, area_bbmp, area_karnataka
import pandas as pd
import json
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np
import pandas as pd
import os
import geopandas as gpd
from shapely.geometry import Point
import os
import boto3
import re


import tempfile
import copy

import warnings
warnings.filterwarnings('ignore')

def get_user_input(prompt, options=None):
    while True:
        if options:
            options_str = ', '.join(map(str, options))
            user_input = input(f"{prompt} ({options_str}): ").strip()

            # Check if the input is a valid index
            if user_input.isdigit() and int(user_input) in options:
                return options[int(user_input)]

        else:
            user_input = input(f"{prompt}: ").strip()

        if not options or user_input in options:
            return user_input
        print("Invalid input. Please try again.")

def parse_month_input(month_input):
    months = []
    for part in month_input.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            months.extend(available_months[start-1:end])
        else:
            months.append(part)
    return ",".join(months)

def download_era5_data(variable, year, month_input, times, region, dataset):
    global region_choice
    month = parse_month_input(month_input)
    print(region)

    print("Downloading:", dataset, variable, year, month, times, region)

    if dataset == 'era5_land':
        data_request = {
                        "format": "netcdf",
                        "variable": variable,
                        "year": year,
                        "month": month.split(','),
                        'time': times,
                        "day": available_days,
                        "area": region,
                        }

        c = cdsapi.Client()
        output_netcdf_file = f"{dataset}_{variable}_{year}_{region_choice}.nc"
        c.retrieve("reanalysis-era5-land", data_request, output_netcdf_file)
    
    else:
        data_request = {
                        "format": "netcdf",
                        "product_type": "reanalysis",
                        "variable": variable,
                        "year": year,
                        "month": month.split(','),
                        'time': times,
                        "day": available_days,
                        "area": region,
                        }

        c = cdsapi.Client()
        output_netcdf_file = f"{dataset}_{variable}_{year}_{region_choice}.nc"
        c.retrieve("reanalysis-era5-single-levels", data_request, output_netcdf_file)

    return output_netcdf_file

def extract_raw_data(netcdf_file, dataset):    
    global region_choice
    ds = xr.open_dataset(netcdf_file)
    df = ds.to_dataframe()
    df.reset_index(inplace=True)

    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month
    df['day'] = df['time'].dt.day
    df['hour'] = df['time'].dt.hour

    df.drop(columns=['time'], inplace=True)

    output_csv_file = f"extracted_{dataset}_{variable}_{year}_{region_choice}.csv"
    df.to_csv(output_csv_file, index=False)
    print(f"CSV file saved: {output_csv_file}")

    return output_csv_file

def coordinates_to_karnataka_hierarchy(df):

    subdistrict_directory = 'geojsons/geojson_KA/subdistricts'
    subdistrict_gdf = gpd.GeoDataFrame()

    for filename in os.listdir(subdistrict_directory):
        if filename.endswith('.geojson'):
            filepath = os.path.join(subdistrict_directory, filename)
            subdistrict_data = gpd.read_file(filepath)
            subdistrict_gdf = pd.concat([subdistrict_gdf, subdistrict_data])

    district_directory = 'geojsons/geojson_KA/districts'
    district_gdf = gpd.GeoDataFrame()

    for filename in os.listdir(district_directory):
        if filename.endswith('.geojson'):
            filepath = os.path.join(district_directory, filename)
            district_data = gpd.read_file(filepath)
            district_gdf = pd.concat([district_gdf, district_data])

    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    df_gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    df_with_subdistrict = gpd.sjoin(df_gdf, subdistrict_gdf, how='left', op='within')
    df_with_subdistrict = df_with_subdistrict.drop(columns=['index_right', 'geometry', 'region_id', 'parent', 'parent_name'])
    df_with_subdistrict.rename(columns={'name': 'subdistrict'}, inplace=True)

    df_with_district = gpd.sjoin(df_gdf, district_gdf, how='left', op='within')
    df_with_district = df_with_district.drop(columns=['index_right', 'geometry', 'region_id', 'parent', 'parent_name'])
    df_with_district.rename(columns={'name': 'district'}, inplace=True)

    df_result = pd.merge(df_with_subdistrict, df_with_district[['district']], left_index=True, right_index=True)
    df_result = df_result[(df_result['subdistrict'].notna()) & (df_result['district'].notna())]
    df_result = df_result.reset_index(drop=True)

    df_result['day'] = df_result['day'].astype(int)
    df_result['month'] = df_result['month'].astype(int)
    df_result['year'] = df_result['year'].astype(int)

    df_result['date'] = pd.to_datetime(df_result[['year', 'month', 'day']])
    df_result.drop(columns=['day', 'month','latitude', 'longitude'], inplace=True)
    
    df_result['week'] = df_result['date'].dt.isocalendar().week
    df_result.sort_values(by=['year', 'date'], ascending=[True, True], inplace=True)

    return df_result

def coordinates_to_bbmp_hierarchy(df):    
    district_directory = 'geojsons/geojson_bbmp'
    district_gdf = gpd.GeoDataFrame()

    for filename in os.listdir(district_directory):
        if filename.endswith('.geojson'):
            filepath = os.path.join(district_directory, filename)
            district_data = gpd.read_file(filepath)
            district_gdf = pd.concat([district_gdf, district_data])

    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    df = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)
    df.drop(columns=['latitude', 'longitude'], inplace=True)
    df = gpd.sjoin(df, district_gdf, how='left', op='within')
    df = df.drop(columns=['index_right', 'geometry', 'region_id', 'parent'])
    df.rename(columns={'name': 'ward'}, inplace=True)

    df = df[(df['parent_name'].notna())]
    df = df.reset_index(drop=True)

    df['day'] = df['day'].astype(int)
    df['month'] = df['month'].astype(int)
    df['year'] = df['year'].astype(int)

    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
    df.drop(columns=['day', 'month'], inplace=True)

    df['week'] = df['date'].dt.isocalendar().week
    df.sort_values(by=['year', 'date'], ascending=[True, True], inplace=True)

    return df

def get_geojsons(region_choice):
    if region_choice == 'Karnataka':
        return coordinates_to_karnataka_hierarchy
    elif region_choice == 'BBMP':
        return coordinates_to_bbmp_hierarchy
    else:
        return None

def process_data(df, variable, region_choice, dataset):
    quarters = [(1, 3), (4, 6), (7, 9), (10, 12)]

    dfs = []

    for quarter in quarters:
        start_month, end_month = quarter
        subset = df[(df['month'] >= start_month) & (df['month'] <= end_month)]

        if not subset.empty:            
            process_spatial = get_geojsons(region_choice)
            if process_spatial:
                df_result = process_spatial(subset)
                dfs.append(df_result)                
            else:
                print(f'No geojsons available for: {region_choice}')
        else:
            print(f"No data selected for months {start_month}-{end_month}")        

    combined_df = pd.concat(dfs, ignore_index=True)
    print('')
    print('Spatial processing and aggregation completed!')
    print('')

    return combined_df

def perform_aggregation(combined_df, year, variable, region_choice, dataset):
    print('')
    aggregation_required = get_user_input('Is temporal aggregation required?: ', ['yes', 'no'])

    if aggregation_required == 'yes':
        if region_choice == 'Karnataka':
            print('')
            column_to_aggregate = get_user_input('Choose a column to aggregate', combined_df.columns.tolist())
            aggregation_type = get_user_input('Please enter the aggregation type required:', ['sum', 'mean'])
            aggregated_data = combined_df.groupby(['subdistrict', 'week']).agg({column_to_aggregate: aggregation_type,
                                                                                'year': 'first',
                                                                                'district': 'first',
                                                                                'date': 'first'
                                                                            }).reset_index()
        elif region_choice == 'BBMP':
            column_to_aggregate = get_user_input('Choose a column to aggregate', combined_df.columns.tolist())
            aggregation_type = get_user_input('Please enter the aggregation type required:', ['sum', 'mean'])
            aggregated_data = combined_df.groupby(['ward', 'week']).agg({column_to_aggregate: aggregation_type,
                                                                                'year': 'first',
                                                                                'parent_name': 'first',
                                                                                'date': 'first'
                                                                            }).reset_index()
            aggregated_data.drop(columns='ward', inplace=True)
        else:
            return None
        
        aggregated_output_filename = f'processed_aggregated_{dataset}_{variable}_{year}_{region_choice}.csv'
        aggregated_data.to_csv(aggregated_output_filename, index=False)
        print('')
        print(f"Data saved to: {aggregated_output_filename}")
        print('')
        print("Done")

    elif aggregation_required == "no":
        if region_choice == 'BBMP':
            if 'ward' in combined_df.columns:
                combined_df.drop(columns='ward', inplace=True)
        
        combined_output_filename = f'processed_{dataset}_{variable}_{year}_{region_choice}.csv'
        combined_df.to_csv(combined_output_filename, index=False)
        print('')
        print(f"Data saved to: {combined_output_filename}")
        print('')
        print("Done")

    else:
        print("Invalid input. Please enter 'yes' or 'no'.")

if __name__ == "__main__":

    global region_choice

    dataset_choice = int(get_user_input("Choose the required dataset - 0: ERA-5 (31km Resolution) | 1: ERA-5 Land (9km Resolution)",[0,1]))
    if dataset_choice == 0:
        dataset = 'era5'
        print('')
        print("Available Variables:")
        for i, variable in enumerate(available_era5_variables):
            print(f"{i}:", variable)
        variable_choice = int(get_user_input("Choose a variable", range(len(available_era5_variables))))
        variable = available_era5_variables[variable_choice]
    else:
        dataset = 'era5_land'
        print('')
        print("Available Variables:")
        for i, variable in enumerate(available_era5_land_variables):
            print(f"{i}:", variable)
        variable_choice = int(get_user_input("Choose a variable", range(len(available_era5_land_variables))))
        variable = available_era5_land_variables[variable_choice]

    print('')
    year = get_user_input("Enter a year:")

    print('')
    month_input = get_user_input("Enter the months (e.g., '1-4,6,9')")
    month = parse_month_input(month_input)

    print('')
    time_input = int(get_user_input("Select frequency - 0:Hourly | 1:4-times/day", [0,1]))
    if time_input == 0:
        times = available_times_hourly
    elif time_input == 1:
        times = available_times_4times
    else:
        print('Please select the appropriate index for time.')

    print('')
    region_choice = int(get_user_input("Choose region - 0:Karnataka | 1:BBMP", [0,1]))
    if region_choice == 0:
        region_choice = "Karnataka"
        region = area_karnataka
    elif region_choice == 1: 
        region_choice = "BBMP"
        region = area_bbmp
    else: 
        print("Invalid region choice. Defaulting to Karnataka")
        region = area_karnataka

    print('')

    output_netcdf_file = download_era5_data(variable, year, month_input, times, region, dataset)
    #output_netcdf_file = '/home/onehealth/ARTPARK/ERA/9KM_Resolution/RawData/dewpoint/era5_land_2m_dewpoint_temperature_2022_Karnataka.nc'
    extracted_raw_data = extract_raw_data(output_netcdf_file, dataset)
    #extracted_raw_data = 'era5_land_2m_dewpoint_temperature_2022_Karnataka.csv'
    input_filename = os.path.basename(extracted_raw_data)
    base_filename, _ = os.path.splitext(input_filename)
    parts = base_filename.split('_')

    variable = '_'.join(parts[2:-2])
    year = parts[-2]
    region_choice = parts[-1]

    df = pd.read_csv(extracted_raw_data)

    combined_df = process_data(df, variable, region_choice, dataset)
    perform_aggregation(combined_df, year, variable, region_choice, dataset)

    print('********** Processing Completed! **********')    
