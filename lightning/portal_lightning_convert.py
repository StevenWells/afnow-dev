import os, sys
import numpy as np
import array
import matplotlib.pyplot as plt
import rasterio, time
from osgeo import gdal
import glob,datetime
from scipy import ndimage
from scipy.ndimage.morphology import binary_dilation

# numbe rof flashes / 15 minutes - datestamp is start of 15 minutes
#origin = 35.975S, 19.975W - lower left
# 
 # deltax= 0.05 degrees
ny = 1440
nx = 1400
orig_N = -35.975+0.05*ny
# kernal
filter = 'dilate' # sobel

overwrite = False
toSdir = False


k = np.zeros((3,3),dtype=int); k[1] = 1; k[:,1] = 1 # for 8-connected
origEPSG='4326'
newEPSG='3857'

dataDir = '/mnt/scratch/cmt/flash_count_test_NRT'
outDir = '/mnt/HYDROLOGY_stewells/geotiff/ssa_mtg_lightning'
tmpDir = '/home/stewells/AfricaNowcasting/tmp'
backupDir = '/mnt/data/hmf/projects/LAWIS/WestAfrica_portal/SANS_transfer/data'



# get recent files
new_files = []
cronFreq=15
t0 = datetime.datetime.today()
#total_files=glob.glob(os.path.join(dataDir,str(t0.year),str(t0.month).zfill(2),'*.gra'))
total_files=glob.glob(os.path.join(dataDir,'*.gra'))

for f in total_files:
	modTimesinceEpoc = os.path.getmtime(f)
	modificationTime = datetime.datetime.fromtimestamp(time.mktime(time.localtime(modTimesinceEpoc)))
	if modificationTime > datetime.datetime.today()-datetime.timedelta(minutes=cronFreq):
		# now check to see if already processed?
		idate = f.split('/')[-1].split('.')[0][:8]
		itime = f.split('/')[-1].split('.')[0][8:12]
		tiffPath = os.path.join(outDir,idate[:8],'mtg_lightning_SSA_'+idate+itime+'_3857.tif')

		if not os.path.exists(tiffPath):     

	#only include if not already processed
			new_files.append(idate+itime)
		elif os.path.exists(tiffPath) and overwrite:
			new_files.append(idate+itime)
if len(new_files)==0:
     		print("No new files to process")
new_files = sorted(new_files)

# now process them
for rundate in new_files:
		print(rundate)
        #getAccs(rundate,accPeriods,dataDir,tmpDir,geotiffDir)
#for idate in dates:	
		filename = os.path.join(dataDir,rundate+'.gra')	
		gen_ints = array.array("f")
		gen_ints.fromfile(open(filename,'rb'),os.path.getsize(filename) // gen_ints.itemsize)
		data = np.array(gen_ints).reshape(ny,nx)
		data[data>0] = 1
	#data[data==0] = np.nan
		if filter=='dilate':
			data_int = data.astype(int)
			sob = binary_dilation(data_int==0, k) & data_int
			sob = ndimage.median_filter(sob,size=2)
		elif filter == 'sobel':	
			sx = ndimage.sobel(data, axis=0, mode='constant')
			sy = ndimage.sobel(data, axis=1, mode='constant')
			sob = np.hypot(sx, sy)
			sob_filter = 2  # original was 2
			sob[sob<=sob_filter] = 0
			sob[sob>sob_filter] = 1
			
		rasFile  = os.path.join(tmpDir,'mtg_lightning_SSA'+idate+'.tif')
		if toSdir:
			rasFile_reproj  = os.path.join(backupDir,'mtg_lightning_SSA_'+rundate+'_3857.tif')
		else:
			rasFile_reproj  = os.path.join(outDir,rundate[:8],'mtg_lightning_SSA_'+rundate+'_3857.tif')
			os.makedirs(os.path.join(outDir,rundate[:8]),exist_ok=True)

		transform = rasterio.transform.from_origin(-19.975,orig_N,0.05,0.05)
		rasImage = rasterio.open(rasFile,'w',driver='GTiff',
                               height=data.shape[0],width=data.shape[1],
                               count=1,dtype=str(data.dtype),
                               crs = 'EPSG:'+str(origEPSG),
                               transform = transform)
		rasImage.write(np.flipud(sob[:]),1)
		rasImage.close()
		ds = gdal.Warp(rasFile_reproj, rasFile, srcSRS='EPSG:'+str(origEPSG), dstSRS='EPSG:'+str(newEPSG), format='GTiff')
		ds = None  
		#os.system('mv '+rasFile+' '+outdir)
		os.system('rm '+rasFile)
