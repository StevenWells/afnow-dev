
import rasterio
import numpy as np
from shapely.geometry import shape
import geopandas as gpd
from rasterio.features import shapes

from shapely.geometry import box,mapping

import json


# Open the GeoTIFF file
with rasterio.open('Observed_CTT_202502100630_extended_3857.tif') as dataset:
    # Get the bounding box of the GeoTIFF
    bbox = box(*dataset.bounds)


gdf1 = gpd.GeoDataFrame({'geometry': [bbox]}, crs=dataset.crs)
gdf1.to_file('geotiff_boundary.shp')


gdf_x = gpd.read_file('negative_values_polygons.shp')

gdf_difference = gdf1.overlay(gdf_x, how='difference')

gdf_difference.to_file('ctt_cutout.shp')

import sys
sys.exit(0)



input_raster_path = 'Observed_CTT_202502100630_extended_3857.tif'
with rasterio.open(input_raster_path) as src:
    raster_data = src.read(1)
    transform = src.transform


    bounds = src.bounds
    crs = src.crs


# Step b: Make a mask to isolate all pixels less than zero
mask = raster_data < 0

# Step c: Make polygon shapefile where each polygon is the boundary of the joining negative-values pixels
# Generate shapes (polygons) from the mask
polygons = shapes(mask.astype(np.int16), transform=transform)

# Create a list to store the polygons
polygon_list = []

for polygon, value in polygons:
    if value == 1:
        polygon_list.append(shape(polygon))

# Create a GeoDataFrame from the list of polygons


bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox]}, crs=crs)

gdf = gpd.GeoDataFrame(geometry=polygon_list,crs=crs)



# Save the GeoDataFrame to a shapefile
output_shapefile_path = 'negative_values_polygons.shp'

gdf = gpd.overlay(gdf, bbox_gdf, how='intersection')


print(gdf)
gdf = gdf[gdf.index == 1947]
print(gdf)

gdf.to_file(output_shapefile_path)


print(f"Polygon shapefile created at {output_shapefile_path}")
