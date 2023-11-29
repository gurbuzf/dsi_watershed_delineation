# Be aware that the variables are case sensitive.

# Two modes can be adopted. 'single' or 'partial'.
# Single Mode: Use when trying to find upstream area of points within a greater watershed.
# Partial Mode: Multiple points in multiple watersheds.
MODE = 'partial'

# The directory of the txt/csv file including outlet points.
# The file must consists of the following headers. ['id', 'name', 'long', 'lat', 'area[km2]']
# id: a unique number identifying a particular point
# name: a unique name for the point.
# long: longitude - lat: latitude
# area: upstream area of the pour point if previously known. If not, leave empty.
OUTLETS = "data/2_stations.csv"


# If single MODE is used, this becomes trivial. This can be set None or empty string "".
WATERSHEDS = "data/vector/simplified_watershed_borders.geojson"

# The rivers with the delineated watershed is cut from the provided river vector file.
# The river network data is expected to be in GeoJSON format
# but other formats supported by Geopandas library should work as well.
# It can be set to '', None or False if no rivers vector provided.
RIVERS = "data/vector/river/TR03.geojson"

# Flow Accumulation Data calculated by QGIS Grass in TIF format
FLOW_ACCUMULATION = "data/acc_grass.tif"

# Drainage Direction Data calculated by QGIS Grass in TIF format
# The data must be created using D8 algorithm and should include digits from 1 to 8 in pixels
DRAINAGE_DIRECTION = "data/dr_dir_grass.tif"

# Two different flow direction codes can be used; "arcgis" or "grass".
# arcgis flow direction uses values ranging from 1 to 128 to represent the eight
# possible flow directions. These values are powers of 2, ranging from 1 to 128.
# 1 (128) represents flow to the east (northeast).

# grass flow direction uses values ranging from 1 to 8 to represent the eight
# possible flow directions.
# 1 (8) represents flow to the northeast (east).
DRAINAGE_DIRECTION_TYPE = "grass"

# True if the progress of the calculations is wanted to be printed out.
VERBOSE = False

# Number of neighboring pixels to consider
# in search of the neigboring pixel with the highest flow accumulation.
# 1 is recommended to reduce the potential deviations from the original pour point.
PIXEL2SEARCH = 1

# The directory where the results to be stored.
RESULTS = "results/"

# The strahler order of rivers less than given will be excluded from river
# vector data to be generated.
# The provided river network attribute table must inlcude 'strahler' column.
MAX_STRAHLER = 1

# The extension of the vector files to be generated.
# "kml" and "geojson" are supported.
VECTOR_EXTENSION = "kml"
