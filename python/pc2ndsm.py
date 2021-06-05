""" convert point cloud elevations to relative heights above DEM """
# TODO some points keep original elevation
import sys
import os.path
from osgeo import gdal
import open3d as o3d
import numpy as np

DEM_NODATA = 0
if len(sys.argv) < 3:
    print("usage: {} dem_file point_cloud min". format(sys.argv[0]))
    sys.exit()
dem_filename = sys.argv[1]
pc_filename = sys.argv[2]
ndsm_min = -9999.
if len(sys.argv) > 3:
    ndsm_min = float(sys.argv[3])
pc_split = os.path.splitext(pc_filename)
out_filename = pc_split[0] + '_ndsm' + pc_split[1]
# get DEM
src_ds = gdal.Open(dem_filename)
dem_max_col = src_ds.RasterXSize - 1
dem_max_row = src_ds.RasterYSize - 1
gt = src_ds.GetGeoTransform()
rb = src_ds.GetRasterBand(1)
dem = rb.ReadAsArray()
# get point cloud
pc = o3d.io.read_point_cloud(pc_filename)
pc_xyz = np.asarray(pc.points)
outlier = []
i = -1
for xyz in pc_xyz:
    i += 1
    #Convert from map to grid indices
    px = min(max(int((xyz[0] - gt[0]) / gt[1]), 0), dem_max_col) #x pixel
    py = min(max(int((xyz[1] - gt[3]) / gt[5]), 0), dem_max_row) #y pixel
    dz = xyz[2] - dem[py, px]
    # filter NODATA and low vegetation
    if dem[py, px] == DEM_NODATA or dz < ndsm_min:
        outlier.append(i)
        continue    # skip nodata 
    xyz[2] = dz
# write out normalized point cloud (elevation from ground)
if len(outlier) > 0:
    pc = pc.select_by_index(outlier, invert=True)
o3d.io.write_point_cloud(out_filename, pc)
