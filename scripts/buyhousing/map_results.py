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
    date_obj = datetime.date.fromordinal(val)
    return date_obj.strftime('%B %d, %Y')

def convert_dates(jsondata):
    for key in jsondata.keys():
        jsondata[key]["date_pulled"] = support.date_convert(jsondata[key]["date_pulled"])
    return jsondata

#NOTE Might need a days to months dict.

class PlotFun:
    def __init__(self, jsondata:dict):
        self.jsondata :dict             = jsondata
        self.gdf      :gpd.GeoDataFrame = self.load_data()
        self.maps     :tuple            = self.load_maps()
        self.gs       :gridspec         = gridspec.GridSpec(nrows=3, ncols=2, height_ratios=[3, 3, 1], width_ratios=[6, 1])
        self.fig      :plt.figure       = plt.figure(figsize=(14, 10))
        self.ax_houses:plt.axes         = self.fig.add_subplot(self.gs[:2, :1], label="mainplot")
        self.ax_radio :plt.axes         = self.fig.add_subplot(self.gs[:2, 1], label="radio")
        self.ax_time  :plt.axes         = self.fig.add_subplot(self.gs[2, :1], label="timeline")
        plt.subplots_adjust(wspace=0.1, hspace=0.2)
        self.radio    :RadioButtons     = RadioButtons(self.ax_radio, tuple(BUTTON_VALS))
        
        self.timestamps = sorted(np.unique([x.toordinal() for x in self.gdf.date_pulled]))
        self.date_slider = Slider(
            self.ax_time, 
            label='days',
            valmin=min(self.timestamps), 
            valmax=max(self.timestamps), 
            valinit=min(self.timestamps),
            orientation="horizontal"
        )
        
        self.plot_update(initial=True)
        self.date_slider.on_changed(self.time_update)
        self.radio.on_clicked(self.radio_update)

        #TODO - Still need a way to load/interact with map data hover points

# FUNCTION Loading functions
    def load_data(self, timespan:int|str = 7):
        filtjson = {}
        if isinstance(timespan, int):
            timeperiod = datetime.datetime.today() - datetime.timedelta(days=timespan)
            for key, val in self.jsondata.items():
                if val["date_pulled"] > timeperiod:
                    filtjson[key] = val
        else:
            filtjson = jsondata
        
        hdf = pd.DataFrame.from_dict(data=filtjson, orient='index')
        gdf = gpd.GeoDataFrame(
            data = hdf, 
            geometry = gpd.points_from_xy(hdf.lat, hdf.long), 
            crs = "EPSG:4326"
        )
        return gdf
    
    def load_maps(self):
        IN_city_map = gpd.read_file("./data/shapefiles/IN_cities/City_and_Town_Hall_Locations_2023.shp")
        IN_county_map = gpd.read_file("./data/shapefiles/IN_counties/County_Boundaries_of_Indiana_2023.shp")
        MI_city_map = gpd.read_file("./data/shapefiles/MI_cities/City.shp")
        MI_county_map = gpd.read_file("./data/shapefiles/MI_counties/Michigan_Counties.shp")
        MI_county_map = MI_county_map.to_crs(epsg=4326)
        MI_city_map = MI_city_map.to_crs(epsg=4326)
        IN_county_map = IN_county_map.to_crs(epsg=4326)
        IN_city_map = IN_city_map.to_crs(epsg=4326)
        return (IN_county_map, MI_county_map, IN_city_map, MI_city_map)

# FUNCTION Update plot
    def time_update(self, val):
        #Need to update listings found on that day in this routine
        self.date_slider.valfmt = format_date(self.date_slider.val)
        self.clear_listings()
        self.plot_update()
        
        self.fig.canvas.draw_idle()
    
    def radio_update(self, val):
        # Handles the radio button updates
        command = self.radio.value_selected
        if command:
            selected = self.date_slider.val
            match command:
                case "days":
                    #Load the last week
                    self.clear_listings()
                    self.gdf = self.load_data(timespan=7)
                    self.plot_update()
                case "weeks":
                    #Load 4 weeks
                    self.clear_listings()
                    self.gdf = self.load_data(timespan=30)
                    self.plot_update()
                case "months":
                    #Load 3 months
                    self.clear_listings()
                    self.gdf = self.load_data(timespan=90)
                    self.plot_update()
                case "all":
                    #Load all data
                    self.clear_listings()
                    self.gdf = self.load_data(timespan="all")
                    self.plot_update()
            
            self.timestamps = sorted(np.unique([x.toordinal() for x in self.gdf.date_pulled]))
            self.date_slider.valmax = max(self.timestamps)
            self.date_slider.valmin = min(self.timestamps)
            self.date_slider.val = selected
        self.fig.canvas.draw_idle()

    def plot_update(self, initial:bool=False):
        
        if initial:
            self.maps[0].plot(ax=self.ax_houses, color="lightgray", edgecolor="black")         #IN_county_map
            self.maps[1].plot(ax=self.ax_houses, color="lightgray", edgecolor="black")         #MI_county_map
            self.maps[2].plot(ax=self.ax_houses, color="magenta", edgecolor="black", alpha=0.6)  #IN_city_map
            self.maps[3].plot(ax=self.ax_houses, color="magenta", edgecolor="black", alpha=0.6)  #MI_city_map
            selected_date = self.date_slider.val
            self.date_slider.valfmt = format_date(selected_date)
        else:
            selected_date = self.date_slider.val

        self.ax_houses.scatter(
            x=self.gdf.long,
            y=self.gdf.lat,
            c='green',
            alpha=0.3,
            label='listings'
        )
        
        condition = (self.gdf.date_pulled.apply(lambda x:x.strftime("%B %d, %Y")) == format_date(selected_date))
        mask = np.where(condition)[0]
        idxs = self.gdf.index[mask]
        temp_df = self.gdf.loc[idxs]
        self.ax_houses.scatter(
            x=temp_df.long,
            y=temp_df.lat,
            c='blue',
            alpha=0.6,
            label='dayselected'
        )        

        # delta = 0.2
        # ax_houses.set_ylim(ymin=gdf.lat.min() - delta, ymax=gdf.lat.max() + delta)
        # ax_houses.set_xlim(xmin=gdf.long.min() - delta, xmax=gdf.long.max() + delta)

    def clear_listings(self):
        remove = []
        for artist in self.ax_houses.get_children():
            if hasattr(artist, "get_label") and artist.get_label() in ("listings", "dayselected"):
                remove.append(artist)

        for artist in remove:
            artist.remove()

    def show_plot(self):
        #Make a custom legend. 
            # legend_elements = [
            #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
            # ]
            
            # ax_houses.legend(handles=legend_elements, loc='upper left')

        plt.tight_layout()
        plt.show()
        print("yay")

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
        jsondata = convert_dates(jsondata)
        logger.info("historical data loaded")
    else:
        logger.warning("No historical data found")
        raise ValueError("Data source not found")

    plots = PlotFun(jsondata)
    plots.show_plot()

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