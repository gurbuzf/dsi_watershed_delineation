# Watershed Delineation Tool :sweat_drops:
Developed for [Turkish State Hydraulic Services (DSI)](https://www.dsi.gov.tr/).


## Description

This tool facilitates the batch processing of pour points, allowing for the on-demand extraction of drainage areas for multiple points.

This Python package has been specifically designed and tested for delineating watersheds in Turkiye. However, with the provision of the necessary data, it can also be utilized for other locations worldwide.

## Data

To be updated!
<!-- - Hydrologicaly conditioned MERIT DEM with approximately 90 meter pixel resolution.
    - 8 digit drainage/flow direction data calculated by QGIS Grass.
    - Flow Accumulation Data calculated by QGIS Grass.
- Vector data produced by GD of Turkish Water Management. 
     - Shapefile of the 25 watershed boundaries in EPSG4326 projection.
     - Shapefile of Countrywide River Network in EPSG4326 projection. -->

## Features

## Installation
1. Clone this repository.
1. Create and activate a virtual environment, using [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) or [pip](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#:~:text=To%20create%20a%20virtual%20environment,virtualenv%20in%20the%20below%20commands.&text=The%20second%20argument%20is%20the,project%20and%20call%20it%20env%20.).
1. Install required libraries.
```sh
pip install -r requirements.txt
```
or
```sh
conda install --file requirements.txt
```
4. Modify the cofiguration.py and run the script:
```sh
python run.py --config_path=configuration.ini
```

## Acknowledgemet
:rocket: ChatGPT :rocket: has played an active role in writing docstrings and enhancing the code.
## Licence
MIT