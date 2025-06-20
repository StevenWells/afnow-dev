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
style = 1 
make_csv = False
toSdir = False
##
#  0 = contours of boundaries from signle 15 minute image
#  1 = pixels are indices based on last hour (4 images): 0 = no lightning
#														 1 = lightning in most recent 0 -> 0 -15 mins
#														 2 = lightning in -15 -> -30
#														 3 = lightning in -30 -> -45
#													     4 = lightning in -45 -> -60
#  Value is based on most recent flash observed
#
#
##


k = np.zeros((3,3),dtype=int); k[1] = 1; k[:,1] = 1 # for 8-connected
origEPSG='4326'
newEPSG='3857'

dataDir = '/mnt/scratch/cmt/flash_count_test_NRT'

outDir = '/mnt/HYDROLOGY_stewells/geotiff/ssa_mtg_lightning_recent'
#outDir= '/home/stewells/AfricaNowcasting/dev/lightning/'
tmpDir='/home/stewells/AfricaNowcasting/dev/lightning/'
#tmpDir = '/home/stewells/AfricaNowcasting/tmp'
backupDir = '/mnt/hmf/projects/LAWIS/WestAfrica_portal/SANS_transfer/data/'


# get recent files
new_files = []
cronFreq=25
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
		tiffPath = os.path.join(outDir,idate[:8],'mtg_lightning_SSA_'+idate+itime+'_recent_3857.tif')

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
		if style ==1:
			nHist = 4
			# get last four images
			dt_now = datetime.datetime.strptime(rundate,"%Y%m%d%H%M")
			backdates = [(dt_now - datetime.timedelta(minutes=15)*x).strftime("%Y%m%d%H%M") for x in range(nHist)]
			backpaths  = [os.path.join(dataDir,x+'.gra') for x in backdates	][::-1]
			sob = np.zeros((ny,nx))
			for idx,ifile in enumerate(backpaths):
				gen_ints = array.array("f")
				#try:
				gen_ints.fromfile(open(ifile,'rb'),os.path.getsize(ifile) // gen_ints.itemsize)
				data = np.array(gen_ints).reshape(ny,nx)
				sob[data>0] = nHist - idx
			if make_csv:
				lats  = [-35.975+0.05*x for x in range(ny)]
				lons = [-19.975 + 0.05*x for x in range(nx)]
				l_inds= np.argwhere(sob)
				with open("lightning_points_"+rundate+".csv",'w') as f:
					f.write('Latitude,Longitude,Window\n')
					for point in range(len(l_inds)):
						f.write(str(round(lats[l_inds[point][0]],3))+','+str(round(lons[l_inds[point][1]],3))+','+str(round(sob[l_inds[point][0],l_inds[point][1]],0))+'\n')
						


			
		if style ==0:
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
			
		rasFile  = os.path.join(tmpDir,'mtg_lightning_SSA'+rundate+'.tif')

		
		if toSdir:
			rasFile_reproj  = os.path.join(backupDir,'mtg_lightning_SSA_'+rundate+'_recent_3857.tif')		
		else:
			rasFile_reproj  = os.path.join(outDir,rundate[:8],'mtg_lightning_SSA_'+rundate+'_recent_3857.tif')
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
		#'os.system('rm '+rasFile)
