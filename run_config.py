# Two modes can be adopted. 'single' or 'partial'.
# Single Mode:
# Partial Mode:

MODE = 'single'

# The directory of the txt file including outlet points.
# The file must be tab limited.
# The file must consists of the following headers. ['id', 'name', 'long', 'lat', 'area[km2]']
## id: a unique number identifying a particular point 
## name: a unique name for the point. 
## long: longitude - lat: latitude
## area: upstream area of the pour point if previously known. If not, leave empty. 
OUTLETS = "../data/outlets.txt"


# If single MODE is used, this becomes trivial. This can be set None or empty string "".
WATERSHEDS = "../data/vector/simplified_watershed_borders.geojson" 

RIVERS = "../data/vector/river/TR03.geojson"

FLOW_ACCUMULATION = "../data/raster/flow_accumulation/TR03.tif"

DRAINAGE_DIRECTION = "../data/raster/drainage_direction/TR03.tif"

# True if the progress of the calculations is wanted to be printed out.
VERBOSE = True 

# Number of neighboring pixels to consider 
# in search of the neigboring pixel with the highest flow accumualtion.
# 1 is recommended to reduce the potential deviations from the original pour point.
PIXEL2SEARCH = 1