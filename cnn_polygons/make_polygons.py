

import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box



from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import numpy as np
from shapely.ops import unary_union

method='joined'

if method=="joined":
    
    with rasterio.open('nowcast_cores_unet_20250619_2100_1hr_3857.tif') as src:
        # Read the data from the file
        data = src.read(1)
        
        # Create a mask for non-missing data (assuming missing data is represented by NaN)
        mask = ~np.isnan(data)
        
        # Extract shapes (polygons) from the mask
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(shapes(data, mask=mask, transform=src.transform))
        )

        # Convert shapes to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(results)

        # Set the coordinate reference system (CRS) to EPSG:3857
        gdf.crs = 'EPSG:3857'
        merged_polygons = unary_union(gdf.geometry)
        # Save the GeoDataFrame to a shapefile
        merged_gdf = gpd.GeoDataFrame(geometry=[merged_polygons], crs='EPSG:3857')
        merged_gdf.to_file('NetNCC_boundaries.shp')
        #gdf.to_file('output_shapefile_joined.shp')



if method=='separate':
    root='nowcast_cores_unet_20250606_1200_1hr_'
    geotiff_files = [root+x+'_4326.tif' for x in ['KY','ZA','SE']]

    polygons = []

    def reproject_geotiff(src_path, dst_path, dst_crs):
        with rasterio.open(src_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(dst_path, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

    # Reproject each GeoTIFF file and create polygons
    for geotiff in geotiff_files:
        reprojected_geotiff = f"reprojected_{geotiff}"
        print(geotiff)
        reproject_geotiff(geotiff, reprojected_geotiff, 'EPSG:3857')
        
        with rasterio.open(reprojected_geotiff) as src:
            # Get the bounding box of the GeoTIFF
            bbox = box(*src.bounds)
            # Append the bounding box to the list of polygons
            polygons.append(bbox)

    # Create a GeoDataFrame with the polygons
    gdf = gpd.GeoDataFrame(geometry=polygons)
    gdf= gdf.set_crs('epsg:3857')

    # Save the GeoDataFrame as a shapefile
    gdf.to_file("geotiff_boundaries_separate.shp")


