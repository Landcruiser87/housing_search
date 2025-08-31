#Import libraries
import numpy as np
import pandas as pd
from os.path import exists
import geopandas as gpd
import geodatasets
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arrow
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox, SpanSelector
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
import support

#Import logger and console from support
from support import logger, console, log_time, get_time

def sir_plots_alot():
    global ax_houses, ax_time, gs, fig
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(nrows=3, ncols=2, height_ratios=[3, 3, 1], width_ratios=[6, 1])
    plt.subplots_adjust(wspace=0.1, hspace=0.2)
    ax_houses = fig.add_subplot(gs[:2, :1], label="mainplot")
    ax_time = fig.add_subplot(gs[2, :2], label="timeline")
    ax_radio = fig.add_subplot(gs[:2, 1], label="radio")
    filtjson = {}
    lastweek = datetime.datetime.today() - datetime.timedelta(days=7)
    for key, val in jsondata.items():
        jsondata[key]["date_pulled"] = support.date_convert(val["date_pulled"])
        if val["date_pulled"] > lastweek:
            filtjson[key] = val

    hdf = pd.DataFrame.from_dict(data=filtjson, orient='index')
    gdf = gpd.GeoDataFrame(
        data = hdf, 
        geometry = gpd.points_from_xy(hdf.lat, hdf.long), 
        crs = "EPSG:4326"
    )
    try:
        IN_city_map = gpd.read_file("./data/shapefiles/IN_cities/City_and_Town_Hall_Locations_2023.shp")
        IN_county_map = gpd.read_file("./data/shapefiles/IN_counties/County_Boundaries_of_Indiana_2023.shp")
        MI_city_map = gpd.read_file("./data/shapefiles/MI_cities/City.shp")
        MI_county_map = gpd.read_file("./data/shapefiles/MI_counties/Michigan_Counties.shp")

        MI_county_map = MI_county_map.to_crs(epsg=4326)
        MI_city_map = MI_city_map.to_crs(epsg=4326)
        IN_county_map = IN_county_map.to_crs(epsg=4326)
        IN_city_map = IN_city_map.to_crs(epsg=4326)

        IN_county_map.plot(ax=ax_houses, color="lightgray", edgecolor="black")
        MI_county_map.plot(ax=ax_houses, color="lightgray", edgecolor="black")
        IN_city_map.plot(ax=ax_houses, color="magenta", edgecolor="black", alpha=0.6)
        MI_city_map.plot(ax=ax_houses, color="magenta", edgecolor="black", alpha=0.6)
        ax_houses.scatter(
            x=gdf.long,
            y=gdf.lat,
            c='blue',
            alpha=0.7,
        )
        delta = 0.2
        # ax_houses.set_ylim(ymin=gdf.lat.min() - delta, ymax=gdf.lat.max() + delta)
        # ax_houses.set_xlim(xmin=gdf.long.min() - delta, xmax=gdf.long.max() + delta)
        # plt.tight_layout()
        plt.show()
        plt.close()

    except Exception as e:
        print(f"{e}")
    #On load, do the following. 
        #1. Load up the last weeks worth of new houses. 
        #2. Include any saved homes and give them a separate icon 
    # days = filter(
    # start_w = ecg_data['section_info'][first_sect]['start_point']
    # end_w = ecg_data['section_info'][first_sect]['end_point']
    # ax_ecg.plot(range(start_w, end_w), wave[start_w:end_w], color='dodgerblue', label='mainECG')
    # ax_ecg.set_xlim(start_w, end_w)
    # ax_ecg.set_ylabel('Voltage (mV)')
    # ax_ecg.set_xlabel('ECG index')
    # ax_ecg.legend(loc='upper left')

    #brokebarH plot for the background of the slider. 
    # ax_time.broken_barh(valid_grouper(valid_sect), (0,1), facecolors=('tab:blue'))
    # ax_time.set_ylim(0, 1)
    # ax_time.set_xlim(0, valid_sect.shape[0])

    # sect_slider = Slider(ax_time, 
    #     label='days',
    #     valmin=first_sect, 
    #     valmax=len(valid_sect), 
    #     valinit=first_sect, 
    #     valstep=1
    # )

    #Radio buttons
    radio = RadioButtons(ax_radio, ('price','sqft','price_sqft', 'price_change','days', 'weeks', 'months'))

    #Set actions for GUI items. 
    # sect_slider.on_changed(update_plot)
    # radio.on_clicked(radiob_action)

    #Make a custom legend. 
    # legend_elements = [
    #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
    # ]
    
    # ax_houses.legend(handles=legend_elements, loc='upper left')
    plt.show()

################################# Start Program ####################################
#Driver code
#FUNCTION Main start
@log_time
def main():
    #Global variables setup
    global jsondata
    fp = "./data/buy_list.json"

    #Load rental_list.json
    if exists(fp):
        jsondata = support.load_historical(fp)
        logger.info("historical data loaded")
    else:
        logger.warning("No historical data found")
        raise ValueError("Data source not found")

    sir_plots_alot()

if __name__ == "__main__":
    main()

#TODO -
# Build this file out to visualize and sort through different dates
# I'd like to have a date select function.  Make it like the slider.py

# Same basic grid layout as slider.py, but the bottom timeline now
# is controlled by datetime.  Not sure how the units will work for that
# might have to use a ref list and keep track of the idx as a global var
# 
# Optional sort conditions.  
    # 1. Be able to sort by most recent, or oldest
    # 2. Have a pop up that shows listing information...
    # 3. Color code cities/zips by amount of listings found.  
    # 4. Have a time window select of the last day, week, month.
    # 5. Be able to save a home so that it always shows up when you're searching.
        # 5b. If a home is saved, go to the individual 
        # page (not sure which source) and save the rest of the 
        # information about the house. 
        # TODO - Figure out all the metrics you would want for a house

    # 6. Export button for saved homes.  
    # 7. Filter by site.
    # 8. If duplicate addresses found, maybe color code the point to how many of the 4 sites its on.   
    # 9. Or have the ability to select quantiles of attributes by site.  
        # - Available
        # - Sqft
        # - price_sqft
        # - price change
        # - price
        # - lotsqft 
        # - time on market
        # - Sold?
# Possible supplimental datasets (Census.gov and BLS.gov)
    # Property Sales
    # Census Demographics
    # Historical Weather
    # Crime Data
    # Public Transit (This one might not work)