import math
import os
import simplekml


def geopandas2KML(gdf, kml_save_path, vector_type):
    """
    Convert a GeoDataFrame to KML.

    Args:
        gdf (geopandas.GeoDataFrame): Input GeoDataFrame.
        kml_save_path (str): Path to save the KML file.
        vector_type (str): Type of vector data ("linestring" or "polygon").

    Returns:
        None

    Raises:
        ValueError: If an unsupported vector_type is provided.

    Example:
        geopandas2KML(gdf, 'output.kml', 'linestring')
    """

    # Retrieve the name of the file without extension
    # kml_name = os.path.basename(kml_save_path).split(".")[0]

    # Get the non-geometry columns
    columns = gdf.columns
    columns = [col for col in columns if col != "geometry"]

    # Create a KML object
    kml = simplekml.Kml(open=1)

    if vector_type == "linestring":
        gdf = gdf.explode(ignore_index=True)
        # Process linestring data
        for index, row in gdf.iterrows():
            linestring = kml.newlinestring(name=str(index))
            linestring.style.linestyle.color = simplekml.Color.hex("0000ff")
            linestring.style.linestyle.width = 3

            for col in columns:
                linestring.extendeddata.newdata(
                    name=col, value=row[col], displayname=col)
            try:
                linestring.coords = row["geometry"].coords[:]
            except NotImplementedError:
                print(row)
                pass

    elif vector_type == "polygon":
        # Process polygon data
        for index, row in gdf.iterrows():
            pol = kml.newpolygon(name=str(index))
            pol.outerboundaryis = list(zip(*row.geometry.exterior.coords.xy))
            pol.style.linestyle.color = simplekml.Color.white
            pol.style.linestyle.width = 2
            pol.style.polystyle.color = simplekml.Color.changealphaint(
                75, simplekml.Color.black)

            for col in columns:
                pol.extendeddata.newdata(
                    name=col, value=row[col], displayname=col)

    else:
        raise ValueError(
            "Unsupported vector_type. Use 'linestring' or 'polygon'.")

    # Save the KML file
    kml.save(kml_save_path)


def haversine_distance(lat1, lon1, lat2, lon2):
    # Earth radius in meters
    earth_radius = 6371000

    # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate the differences in latitude and longitude
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * \
        math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = earth_radius * c

    return distance
