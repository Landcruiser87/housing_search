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


def date_convert():
    pass

def sir_plots_alot():
    global ax_houses, ax_time, gs, fig
    # fig = plt.figure(figsize=(16, 10))
    # gs = gridspec.GridSpec(nrows=3, ncols=2, height_ratios=[3, 3, 1], width_ratios=[5, 1])
    # plt.subplots_adjust(hspace=0.40)
    # ax_houses = fig.add_subplot(gs[:2, 0], label="mainplot")
    # ax_time = fig.add_subplot(gs[3, :2], label="timeline")
    # ax_options = fig.add_subplot
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
    ax_time = fig.add_subplot(gs[1, :2])
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

    #Add axis container for radio buttons
    ax_radio = plt.axes([0.905, .33, 0.09, 0.32])

    #Radio buttons
    radio = RadioButtons(ax_radio, ('Base Figure', 'Roll Median', 'Add Inter', 'Hide Leg', 'Show R Valid', 'Overlay Main', 'Overlay Inner', 'Frequency-Stem', 'Frequency-Spec', 'Stumpy Search'))

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