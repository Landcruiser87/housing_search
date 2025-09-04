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
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, Arrow
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox, SpanSelector

#Import logger and console from support
from support import logger, console, log_time, get_time
import support

BUTTON_VALS = ['price','sqft','price_sqft', 'price_change', 'saved', 'days', 'weeks', 'months', 'all']

def format_date(val):
    """
    Formats a timestamp to a "Month Day, Year" string.
    """
    date_obj = datetime.date.fromordinal(int(val))
    return date_obj.strftime('%B %d, %Y')

def sir_plots_alot():
# FUNCTION Update plot
    def update_plot(val):
        # Handles the plot updating
        #If you chose anything except frequency or stumpy, clear main axis and redraw it in its original form
        # BUTTON_VALS = ['price','sqft','price_sqft', 'price_change', 'saved', 'days', 'weeks', 'months', 'all']
        command = radio.value_selected
        if command:
            match command:
                case [*BUTTON_VALS] if command in [BUTTON_VALS[:3]]:
                    logger.info("first 3")
                    # if check_axis("mainplot"):
                    #     ax_ecg.cla()
                    # else:
                    #     ax_ecg = fig.add_subplot(gs[0, :2], label="mainplot")
                    # update_main()

                case 'saved':
                    logger.info("saved")

                case [*BUTTON_VALS] if command in [BUTTON_VALS[:-3]]:
                    logger.info("last 3")
        
        date_slider.valfmt = format_date(date_slider.val)
        fig.canvas.draw_idle()

#     #FUNCTION Radio Button Actions
#     def radiob_action(val):
#         sect = sect_slider.val
#         start_w = ecg_data['section_info'][sect]['start_point']
#         end_w = ecg_data['section_info'][sect]['end_point']

#         if val in ["Base Figure", "Roll Median", "Add Inter", "Hide Leg", "Show R Valid"]:
#             #When selecting various functions.
#             #This is to make sure you remove the appropriate axis' before redrawing the main chart
#             if configs["freq"] and check_axis("freq_list"):
#                 remove_axis(["freq_list", "ecg_small"])
#                 configs["freq"] = False
#                 update_plot(val)
                
#             if configs["overlay"] and check_axis("overlays"):
#                 remove_axis(["overlays", "ecg_small"])
#                 configs["overlay"] = False
#                 update_plot(val)
                
#             if configs["stump"] and check_axis("stumpy"):
#                 remove_axis(["stumpy", "dist_locs", "ecg_small"])
#                 configs["stump"] = False
#                 update_plot(val)

#         if val == 'Roll Median':	
#             ax_ecg.plot(range(start_w, end_w), utils.roll_med(wave[start_w:end_w]), color='orange', label='Rolling Median')
#             ax_ecg.legend(loc='upper left')

#         elif val == 'Add Inter':
#             inners = ecg_data['interior_peaks'][(ecg_data['interior_peaks'][:, 2] >= start_w) & (ecg_data['interior_peaks'][:, 2] <= end_w), :]
#             for key, val in PEAKDICT_EXT.items():
#                 if inners[np.nonzero(inners[:, key])[0], key].size > 0:
#                     ax_ecg.scatter(inners[:, key], wave[inners[:, key]], label=val[0], color=val[1], alpha=0.8)
#             ax_ecg.set_title(f'All interior peaks for section {sect} ', size=14)
#             ax_ecg.legend(loc='upper left')

#         elif val == 'Hide Leg':
#             ax_ecg.get_legend().remove()

#         elif val == 'Show R Valid':
#             Rpeaks = ecg_data['peaks'][(ecg_data['peaks'][:, 0] >= start_w) & (ecg_data['peaks'][:, 0] <= end_w), :]
#             for peak in range(Rpeaks.shape[0]):
#                 if Rpeaks[peak, 1] == 0:
#                     band_color = 'red'
#                 else:
#                     band_color = 'lightgreen'
#                 rect = Rectangle(
#                     xy=((Rpeaks[peak, 0] - 10), (wave[Rpeaks[peak,0]] + wave[Rpeaks[peak,0]]*(0.05)).item()), 
#                     width=np.mean(np.diff(Rpeaks[:, 0])) // 6, 
#                     height=wave[Rpeaks[peak, 0]].item() / 10,
#                 facecolor=band_color,
#                 edgecolor="grey",
#                 alpha=0.7)
#                 ax_ecg.add_patch(rect)

#         elif 'Frequency' in val:
#             configs["freq"] = True
#             frequencytown()

#         elif val == 'Overlay Main':
#             configs["overlay"] = True
#             overlay_r_peaks(True)

#         elif val == 'Overlay Inner':
#             configs["overlay"] = True
#             overlay_r_peaks()

#         elif val == 'Stumpy Search':
#             configs["stump"] = True
#             wavesearch()

#         fig.canvas.draw_idle()    

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
    dates = []
    # try:
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
    radio = RadioButtons(ax_radio, tuple(BUTTON_VALS))

    # except Exception as e:
    #     print(f"{e}")
    timestamps = sorted(np.unique([x.toordinal() for x in gdf.date_pulled]))
    #brokebarH plot for the background of the slider. 
    # ax_time.broken_barh(valid_grouper(valid_sect), (0,1), facecolors=('tab:blue'))
    date_slider = Slider(ax_time, 
        label='days',
        valmin=timestamps[0], 
        valmax=timestamps[-1], 
        valinit=timestamps[0],
    )
    date_slider.valfmt = format_date(date_slider.val)
    # ax_time.set_ylim(0, 1)
    # ax_time.set_xlim(timestamps[0], timestamps[-1])

    #Radio buttons

    #Set actions for GUI items. 
    date_slider.on_changed(update_plot)
    # radio.on_clicked(radiob_action)


    plt.show()
    plt.close()


    #Make a custom legend. 
    # legend_elements = [
    #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
    # ]
    
    # ax_houses.legend(handles=legend_elements, loc='upper left')

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
    # Property Sales surrounding?  Not sure how to find that
    # Census Demographics
    # Historical Weather, going back a few years maybe
    # Crime Data
    # Public Transit (This one might not work)
    # Sales for the last 5 years in the same area?
    # Water reports
    # Soil reports. 
    # Could an LLM find all this?  meh