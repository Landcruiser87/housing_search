
import numpy as np
import pandas as pd
import support
import json
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
SWITCH_SITE = {
    "Zillow":"www.zillow.com",
    "Redfin":"www.redfin.com",
    "Craigs":"www.craigslist.org",
    "Apartments":"www.apartments.com",
    "Homes":"www.homes.com", 
    "Realtor":"www.realtor.com"
}
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
        """Date conversion from a string to a np.datetime64

        Args:
            dt_str (str): Datetime string 

        Returns:
            npdateOb (np.datetime64): a datetime object
        """        
        if isinstance(dt_str, str):
            dateOb = datetime.datetime.strptime(dt_str.split("_")[0],'%m-%d-%Y')
            npdateOb = np.datetime64(dateOb, "D")
            return npdateOb
        else:
            return np.nan
    
    def neighborhood_convert(neigh:str):
        """neighborhoods in the dataset need a little formatting. 

        Args:
            neigh (str): _description_

        Returns:
            _type_: _description_
        """        
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

    
    #Load data frame:
    data = pd.DataFrame.from_dict(json_f, orient="index")
    #Convert Dates to np.datetime64s
    data["date_pulled"] = data["date_pulled"].apply(date_convert)
    #Unify neighborhoods
    data["neigh"] = data["neigh"].apply(neighborhood_convert)
    

    #Set types for strings
    for col in ["source","neigh", "address"]:
        data[col] = data[col].astype(str)
    #Set types for floats
    for col in ["price", "bed", "bath"]:
        data[col] = data[col].astype(float)
    #replace bs in lat long and turn to float
    for col in ["lat", "long"]:
        data[col] = data[col].replace(r'^\s*$', np.nan, regex=True)
        data[col] = data[col].astype(float)

    return data

def load_graph():
    
    ################## widget functions ###############################
    def checkb_site_action(val):
        update_main()
        #update main data and trend plot below
        #need to remove the val from that target.  
        #won't have a ref to the line...  ohhhh what about this.  
            #Nest the option box INSIDE the legend for site.  
            #then have the outer box be for neighborhood giving you some more space.  
        fig.canvas.draw_idle()

    def checkb_neigh_action(val):
        update_main()
        #update main data and trend plot below
        fig.canvas.draw_idle()

    def get_active_labels():
        actives = []
        for chkb_name, artist in zip(["site", "neigh"], [checkb_site, checkb_neigh]):
            for label in artist.get_checked_labels():
                actives.append((chkb_name, label))
        
        return actives
    ################## plot functions ###############################

    def data_transform(df:pd.DataFrame, metric:str):
        #Determine whether we're using neighborhoods or zips
        area = check_m_type.get_checked_labels()[0]
        if area == "Neighborhood":
            df_prime = chi_data["neigh"].merge(
                right = df,
                on = "neigh",
                how = "outer",
                validate = "m:m"
            )
            #TODO - Could merge neigh on secondary neighborhood, but just amend the to include
            #the missing neighborhoods in the first one!  ha!  donezo and easy and 
            #takes care of their group assignment
        
        elif area == "Zip":
            df_prime = chi_data["zip"].merge(
                right = df,
                on = "zip",
                how = "outer",
                validate = "m:m"
            )        
        if metric.startswith("Listing"):
            pass
        elif metric.startswith("Price"):
            #I want to return prices for that neighborhood
            pass
        elif metric.startswith("Population"):
            pass
        elif metric.startswith("Health"):
            pass


    def update_main(xmin:datetime=None, xmax:datetime=None):
        #Get active labels in the checkboxes
        labels = get_active_labels()
        tickslabels = sp_section.get_xticklabels()
        if not span._selection_completed:
            mindate = datetime.datetime.strptime(tickslabels[0].get_text(), "%Y-%m-%d")  
            maxdate = datetime.datetime.strptime(tickslabels[-1].get_text(), "%Y-%m-%d")
        else:
            mindate = xmin
            maxdate = xmax

        source, neigh = [], ["chicago"]
        for cbox, label in labels:
            if cbox == "site":
                source.append(SWITCH_SITE[label])
            elif cbox == "neigh":
                neigh.append(" ".join(label.lower().split()))
        #Create boolean masks for each filter in the first two listboxes
        source_mask = data["source"].isin(source)
        neigh_mask = data["neigh"].isin(neigh)
        dmin_mask = data["date_pulled"] >= np.datetime64(mindate, "D")
        dmax_mask = data["date_pulled"] <= np.datetime64(maxdate, "D")
        idx_mask = source_mask & neigh_mask & dmin_mask & dmax_mask
        filtdata = data[idx_mask].copy()

        #Now filter and join wth chi_data depending on selection. 
        #Need the ability to select different analysis blocks
        metric_val = checkb_metric.value_selected
        df = data_transform(filtdata, metric_val)
        df.plot(ax=sp_map)
        sp_map.set_title(f"{metric_val}")

        # fig.canvas.draw_idle()

    def cycle_time():
        global tw, amount
        amount = TIME_DICT[tw]
        tw = next(TIME_WINDOW)
        update_main()
        #Need a mainplot update here

    def onselect_func(x_min, x_max):
        xmind = mdates.num2date(x_min)
        xmaxd = mdates.num2date(x_max)

        # region_x = np.timedelta64(xmin, xmax)
        # print(f"{xmin:%Y-%m-%d} | {xmax:%Y-%m-%d}")
        # #early terminate if you accidentally click
        # if xmin==xmax or len(region_x) <= 10:
        #     raise ValueError(f'Please select a larger range than {len(region_x)}')
        update_main(xmind, xmaxd)
        #Have this update the choloropeth map and the trendline. 
    
    def check_m_type_action():
        #eventually will switch underlying dataset from zips to neighborhoods
        pass

    def checkb_metric_action():
        pass

    ################## Loading plot objects ###############################
    global sp_map, sp_trend, sp_section, gs, tw
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(nrows=3, ncols=2, height_ratios=[4, 2, 1], width_ratios=[5, 1])
    plt.subplots_adjust(hspace=0.2)
    sp_map = fig.add_subplot(gs[0, 0], label="mainplot")
    rax = sp_map.inset_axes([0.0, 0.0, 0.15, 0.17])
    boxcolors = ["blue", "green"]
    check_m_type = CheckButtons(
        ax = rax,
        labels = ["Neighborhood", "Zip"],
        actives = [True, False], 
        label_props = {"color":boxcolors},
        frame_props = {"edgecolor":boxcolors},
        check_props = {"facecolor":boxcolors}
    )
    sp_trend = fig.add_subplot(gs[1, 0], label="trendline")
    sp_section = fig.add_subplot(gs[2, 0], label="dateselector")
    #Set initial axis values for a date
        #Maybe flip them into the graph too to make it a chart on its own!  ooooo yes.

    xmax = np.max(data["date_pulled"])
    #Subset the last 4 weeks to start
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
    ax_check_site = plt.axes([0.74, 0.75, 0.20, 0.13], label="radio_site")
    ax_check_neigh = plt.axes([0.74, 0.49, 0.20, 0.26], label="radio_neigh")
    ax_radio_metric = plt.axes([0.74, 0.25, 0.20, 0.20], label="radio_metric")
    ax_cycletime = plt.axes([0.74, 0.11, 0.20, 0.10], label="radio_cycle")

    #Button for cycling Time window
    cycle_time_button = Button(ax_cycletime, label='Cycle Time Window')

    #Make Check buttons (enabled) and radio buttons
    checkb_site = CheckButtons(
        ax = ax_check_site, 
        labels = tuple(SITES),
        actives = [True] * len(SITES),
        label_props = {
            "fontsize":[11] * len(SITES),
            "fontweight":["bold"] * len(SITES)
        }
    )
    checkb_neigh = CheckButtons(
        ax = ax_check_neigh, 
        labels = tuple(AREAS),
        actives = [True] * len(AREAS),
        label_props = {
            "fontsize":[11] * len(AREAS),
            "fontweight":["bold"] * len(AREAS)
        }
    )
    checkb_metric = RadioButtons(
        ax = ax_radio_metric, 
        labels = ("Listing Frequency", "Price", "Population", "Health", "Crime"),
        active = 0
    )
    
    #IDEA: It would be cool to see amount of reposts too across different sites and their own
    ################## Loading plots ###############################
    global tw, amount
    tw = "day"
    amount = TIME_DICT[tw]
    update_main()
    # update_trend(tw, amount)

    #Set actions for GUI items.     
    span.on_changed(onselect_func)
    cycle_time_button.on_clicked(cycle_time)        

    #Main checkbutton actions
    check_m_type.on_clicked(check_m_type_action)
    checkb_site.on_clicked(checkb_site_action)      
    checkb_neigh.on_clicked(checkb_neigh_action)    
    checkb_metric.on_clicked(checkb_metric_action)  
    
    #Make a custom legend. 
    # legend_elements = [
    #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
    #     ]
    # sp_trend.legend(handles=legend_elements, loc='upper left')

    #show the plot!
    plt.show()

def main():
    #Load historical json
    fp = PurePath(Path.cwd(), Path(f"./data/rental_list.json"))
    json_f = support.load_historical(fp)

    global data, chi_data
    #Load city data from data.cityofchicago.org 
    chi_data = support.socrata_api() #Pass in True to update city data
    #Load / clean data into a df
    data = clean_data(json_f)
    #Load GUI
    graph = load_graph()

if __name__ == "__main__":
    main()


#NOTES
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

