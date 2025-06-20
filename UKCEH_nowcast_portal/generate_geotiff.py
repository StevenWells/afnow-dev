
import numpy as np
import u_interpolate as uinterp
import rasterio, os
from osgeo import gdal
import shlex, subprocess


class UKCEH_PortalProduct:
    def __init__(self,user,product,crs='EPSG:4326',root="./UKCEH_nowcast_portal",units="%"):
        self.user = user
        self.product = product
        self.units = units
        self.crs = crs
        self.root = root



    def generate_portal_geotiff(self,image,lats,lons,originTime,leadTime,outFile =None,irregular=True,dx =None):
        """
        resample image onto a fixed resolution array
        IN: image   : 2-D numpy array of image to be resampled onto a fixed grid
        IN: lats    : 2-D numpy array of irregular latitude points (same size as image)
        IN: lons    : 2-D numpy array of irregular longitude points (same size as image)
        IN: originTime: datetime object of origin validity time of image
        IN: leadTime:  integer indicating  lead time from origin in number of minutes 
        IN: outFile (optional) : Output path and filename of final geotiff File
        IN: irregular (optional): Are the lat-long coordinates on an irregular grid (non-constant pixel size). If so, data will be reprojected
        IN: dx (optional) : If irregular, can specify fixed resolution to project only. If not specified, average pixel size from irregular grid will be used

        OUT: Geotiff file in self.root folder, under datestamped subfolder, unless location specified specifically by outFile
        """
        leadTime = str(leadTime)
        if outFile is None:
            # assume it will be the main portal Directory
            outDir = os.path.join(self.root,self.user+'_'+self.product,originTime.strftime("%Y%m%d"))
            os.makedirs(outDir,exist_ok=True)
            outBasename = 'nowcast_'+originTime.strftime("%Y%m%d_%H%M_")+leadTime.zfill(4)+'.tif'
            outFile = os.path.join(outDir,outBasename)
        else:
            os.makedirs(os.path.dirname(outFile),exist_ok=True)



        lat_min, lat_max= np.nanmin(lats),np.nanmax(lats)
        lon_min, lon_max= np.nanmin(lons),np.nanmax(lons)

        if irregular:
            # need to resample

            # Use dx for resolution if supplied, else use lat, lon mean of  (max-min)/number of cells
            if dx is None:
                av_lat = (lat_max - lat_min)/lats.shape[1]
                av_lon = (lon_max - lon_min)/lats.shape[0]
                dx = (av_lat+av_lon)/2.0
            

            fixed_lats = np.arange(lat_min,lat_max ,dx)
            fixed_lons = np.arange(lon_min,lon_max ,dx)
            grid_lon, grid_lat = np.meshgrid(fixed_lons,fixed_lats)

            inds, weights, new_shape=uinterp.interpolation_weights(lons[np.isfinite(lons)], lats[np.isfinite(lats)],grid_lon, grid_lat, irregular_1d=True)
            data_interp=uinterp.interpolate_data(image, inds, weights, new_shape)

        else:
            grid_lon, grid_lat = np.meshgrid(lons,lats)
            dx = (lat_max - lat_min)/lats.shape[1]
            data_interp = image


        transform = rasterio.transform.from_origin(lon_min,lat_max,dx,dx)


        if self.crs.lower()!='epsg:3857':
            rasFile = os.path.splitext(outFile)[0]+'_tmp.tif'
        else:
            rasFile = outFile
        rasImage = rasterio.open(rasFile,'w',driver='GTiff',
                                    height=data_interp.shape[0],width=data_interp.shape[1],
                                    count=1, dtype= str(data_interp.dtype),
                                    crs = self.crs,
                                    nodata=-999.9,
                                    transform = transform
                                    )   
        rasImage.write(np.flipud(data_interp[:]),1)
        rasImage.close()   

        # now reproject if required and remove tmp
        if self.crs.lower()!='epsg:3857':
            ds = gdal.Warp(outFile, rasFile, srcSRS=self.crs, dstSRS='EPSG:3857', format='GTiff',creationOptions=["COMPRESS=DEFLATE", "TILED=YES"])
            ds = None 
            os.system('rm '+rasFile)


        # Include some Metatdata
       # xmp_metadata = f"""xml:XMP=<x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'><rdf:Description rdf:about='' xmlns:xmp='http://ns.adobe.com/xap/1.0/' xmlns:dc='http://purl.org/dc/elements/1.1/'><dc:title><rdf:Alt><rdf:li xml:lang='en'>{self.product}</rdf:li></rdf:Alt></dc:title><dc:creator><rdf:Seq><rdf:li>{self.user}</rdf:li></rdf:Seq></dc:creator><dc:description><rdf:Alt><rdf:li xml:lang='en'>Units: {self.units}</rdf:li></rdf:Alt></dc:description></rdf:Description></rdf:RDF></x:xmpmeta>"""
        
        xmp_metadata = f"""xml:XMP=<x:xmpmeta xmlns:x=\'adobe:ns:meta/\'>
        <rdf:RDF xmlns:rdf=\'http://www.w3.org/1999/02/22-rdf-syntax-ns#\'>
            <rdf:Description rdf:about=\'\' xmlns:xmp=\'http://ns.adobe.com/xap/1.0/\' xmlns:dc=\'http://purl.org/dc/elements/1.1/\'>
            <dc:title><rdf:Alt><rdf:li xml:lang=\'en\'>{self.product}</rdf:li></rdf:Alt></dc:title>
            <dc:creator><rdf:Seq><rdf:li>{self.user}</rdf:li></rdf:Seq></dc:creator>
            <dc:description><rdf:Alt><rdf:li xml:lang=\'en\'>Units: {self.units}</rdf:li></rdf:Alt></dc:description>
            </rdf:Description>
        </rdf:RDF>
        </x:xmpmeta>"""
        metadata_option = f"-mo {shlex.quote(xmp_metadata)}"
        subprocess.run(f"gdal_edit.py {outFile} {metadata_option}", shell=True, check=True)
        #os.system("gdal_edit.py -mo "+xmp_metadata+" "+outFile)

