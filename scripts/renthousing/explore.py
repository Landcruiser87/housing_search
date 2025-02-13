#For looking at housing data over the past few years. 
#Could chart a few different variables, 

#Main things i want.  

#Slider on the bottom to navigate time. 
    #Gonna be a bitch with datetimes. 
    #Time regrouping.  Need resolutions at the day, week, month level for changing trend

#Dual charts residing above. 
#On the left.
    #Main map chart.  (plotly would be better here but lets be OG MPL)
    #For the time period selected, show possible rent dots 
    #Color by count frequency of availble rentals
    #? Ability to click neighborhood and have the 
        #corresponding right graph filter to that data?  ooo smooth! 

#On the right - Option button to the right to flip between the following
    #1. Show price trend.  Tie that to the brokebarh as well for time selection
        #Would be for all neighborhoods indvidually and averaged over the search area.

    #2. Neighborhood listing frequencies.  
        # Break out the top 10 neighborhoods in a bar chart maybe?
        #Color by safety ratings?
            #Data won't be as complete, but would be interesting to see. 
    #3. Sites that repeat listings?  meh

#On the bottom
#Brokebarh chart with a time span selector.  
    #That would be sweet. and would take care of my time regrouping needs all in one object. 
        #NOTE - I might need neighborhood polygons..  Which the city has stored I think on their API...

# import matplotlib
# matplotlib.use('TkAgg')
# import scipy.signal as ss
# import stumpy 
import numpy as np
import pandas as pd
import support
import datetime
import geopandas as gpd
from itertools import cycle
from pathlib import Path, PurePath
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Arrow
from matplotlib.widgets import CheckButtons, Button, RadioButtons, SpanSelector, TextBox

#Neighborhoods searched
AREAS = [
    'Portage Park',    
    'Ravenswood',
    'Irving Park',     
    'Albany Park',     
    'North Center',    
    'North Park',      
    'Lincoln Square',  
    'Avondale',        
    'Wicker Park',     
    'Roscoe Village',
    'Budlong Woods',
    'Mayfair',
]
#Sites Searched
SITES = ["Zillow", "Redfin", "Craigs", "Apartments", "Homes", "Realtor"]

#Time Window cycle options
TIME_WINDOW = cycle(["day", "week", "month", "year"])
TIME_DICT = {
    "day":7,
    "week":4, 
    "month":6,
    "year":2
}
#Load a logger instance
# logger = support.get_logger("", support.console)

#FUNCTION Convert Date
def clean_data(json_f:dict) -> pd.DataFrame:
    def date_convert(dt_str:str):
        if isinstance(dt_str, str):
            dateOb = datetime.datetime.strptime(dt_str.split("_")[0],'%m-%d-%Y')
            npdateOb = np.datetime64(dateOb, "D")
            return npdateOb
        else:
            return np.nan
    def neighborhood_convert(neigh):
        # names =[name.lower() for name in np.unique(maps["pri_neigh"])]
        if "-" in neigh:
            neigh = " ".join(neigh.split("-"))
        return neigh.lower()

            #BUG 
                #Need a better way to do this. 
                #Could use Levensetein distance with a low threshold

            # ['Albany-Park', 'Avondale', 'Budlong-Woods', 'Budlong-WoodsMayfair',
            #  'Irving-Park', 'Lincoln-Square', 'Mayfair', 'North-Center',
            #  'North-Park', 'Portage-Park', 'Ravenswood', 'Roscoe-Village',
            #  'Wicker-Park', 'albany-park', 'avondale', 'budlong-woods',
            #  'budlong-woodsmayfair', 'chicago', 'irving-park', 'lincoln-square',
            #  'mayfair', 'north-center', 'north-park', 'portage-park', 'ravenswood',
            #  'roscoe-village', 'wicker-park']

    #Load data frame
    data = pd.DataFrame.from_dict(json_f, orient="index")
    #Convert Dates to np.datetime64s
    data["date_pulled"] = data["date_pulled"].apply(date_convert)
    #Unify neighborhoods
    data["neigh"] = data["neigh"].apply(neighborhood_convert)

    return data

def load_graph():
    
    ################## widget functions ###############################

    def check_site_action():
        pass

    def check_neigh_action():
        pass

    ################## plot functions ###############################

    def update_main(time_window:str, amount:int):
        pass

    def cycle_time():
        amount = TIME_DICT[tw]
        tw = next(TIME_WINDOW)
        update_main(tw, amount)
        #Need a mainplot update here

    def onselect_func(xmin, xmax):
        xmin = mdates.num2date(xmin)
        xmax = mdates.num2date(xmax)
        # region_x = np.timedelta64(xmin, xmax)
        # print(f"{xmin:%Y-%m-%d} | {xmax:%Y-%m-%d}")
        # #early terminate if you accidentally click
        # if xmin==xmax or len(region_x) <= 10:
        #     raise ValueError(f'Please select a larger range than {len(region_x)}')

        #Have this update the choloropeth map and the trendline. 

    ################## Loading plot objects ###############################
    global sp_map, sp_trend, sp_section, gs, tw
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(nrows=3, ncols=2, height_ratios=[4, 2, 1], width_ratios=[5, 1])
    plt.subplots_adjust(hspace=0.2)
    sp_map = fig.add_subplot(gs[0, 0], label="mainplot")
    sp_trend = fig.add_subplot(gs[1, 0], label="trendline")
    sp_section = fig.add_subplot(gs[2, 0], label="dateselector")
    #Set initial axis values for a date
        #Maybe flip them into the graph too to make it a chart on its own!  ooooo yes.

    #TODO initial plot loading here of presets. 
    tw = "day"
    amount = TIME_DICT[tw]
    # update_main(tw, amount)
    # update_trend(tw, amount)

    xmax = np.max(data["date_pulled"])
    #Subset the last 14 days to start
    xmin = np.max(data["date_pulled"]) - np.timedelta64(4, "W")
    sp_section.set_xlim(xmin, xmax)
    sp_section.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    sp_section.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ticks = sp_section.get_xticks() #weird error here that if i don't set the ticks before i set the labels it throws a warning???  oooooooooook
    sp_section.set_xticks(ticks)
    tickslabels = sp_section.get_xticklabels()
    sp_section.set_xticklabels(tickslabels, rotation=40)

    span = SpanSelector(
        sp_section,
        onselect_func,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.5, facecolor="tab:orange"),
        interactive=True,
        drag_from_anywhere=True
    )

    #Add total / indivdual containers for radio buttons
    # ax_widgets = fig.add_subplot(gs[:, 1], label="widget_ax")
    ax_radio_site = plt.axes([0.74, 0.75, 0.20, 0.13], label="radio_site")
    ax_radio_neigh = plt.axes([0.74, 0.49, 0.20, 0.26], label="radio_neigh")
    ax_radio_metric = plt.axes([0.74, 0.25, 0.20, 0.20], label="radio_metric")
    ax_cycletime = plt.axes([0.74, 0.11, 0.20, 0.10], label="radio_cycle")

    #Button for cycling Time window
    cycle_time_button = Button(ax_cycletime, label='Cycle Time Window')

    #Make Check buttons (enabled) and radio buttons
    checkb_site = CheckButtons(
        ax = ax_radio_site, 
        labels = tuple(SITES),
        actives = [True] * len(SITES),
        label_props = {
            "fontsize":[11] * len(SITES),
            "fontweight":["bold"] * len(SITES)
        }
    )
    checkb_area = CheckButtons(
        ax = ax_radio_neigh, 
        labels = tuple(AREAS),
        actives = [True] * len(AREAS),
        label_props = {
            "fontsize":[11] * len(AREAS),
            "fontweight":["bold"] * len(AREAS)
        }
    )
    radio_metric = RadioButtons(
        ax = ax_radio_metric, 
        labels = ("Listing Frequency", "Price", "Price Regression", "Agg Crime Score", "Avg Sqft"),
        active = 0
    )
    
    #Set actions for GUI items. 
    # span.on_changed(update_maincharts)            #TODO write update_maincharts  
    cycle_time_button.on_clicked(cycle_time)        #TODO write cycle_back
    checkb_site.on_clicked(check_site_action)       #TODO write radio_site_action
    checkb_area.on_clicked(check_neigh_action)      #TODO write radio_neigh_action
    # radio_metric.on_clicked(radio_metric_action)  #TODO write radio_metric_action
    
    #Make a custom legend. 
    # legend_elements = [
    #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
    #     ]
    # sp_trend.legend(handles=legend_elements, loc='upper left')


    #show the plot!
    plt.show()

def main():
    #Load historical data and load into dataframe
    fp = PurePath(Path.cwd(), Path(f"./data/rental_list.json"))
    json_f = support.load_historical(fp)

    #Load official neighborhood polygons from data.cityofchicago.org
    global data, maps
    maps = support.load_neigh_polygons() 
    
    #clean data
    data = clean_data(json_f)

    #Load GUI
    graph = load_graph()

if __name__ == "__main__":
    main()