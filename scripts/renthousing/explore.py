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
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arrow
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox, SpanSelector
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
from pathlib import Path, PurePath
from itertools import cycle
import support

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

SITES = ["zillow", "redfin", "craigs", "apartments", "homes", "realtor"]

def load_graph():
    ################## plot functions ###############################
    def onselect():
        pass
        #Have this update the choloropeth map and the trendline. 
    ################## Loading plot objects ###############################
    global sp_map, sp_trend, sp_section, gs
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(nrows=4, ncols=2, height_ratios=[1, 3, 3, 1], width_ratios=[3, 1])
    plt.subplots_adjust(hspace=0.2)
    sp_map = fig.add_subplot(gs[0, 0], label="mainplot")
    sp_trend = fig.add_subplot(gs[1, 0], label="trendline")
    sp_section = fig.add_subplot(gs[2, 0], label="dateselector")

    span = SpanSelector(
        sp_section,
        onselect,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.5, facecolor="tab:orange"),
        interactive=True,
        drag_from_anywhere=True
    )
    #Invalid step axes placeholders
    
    time_windows = cycle(["day", "week", "month"])

    #Add containers for radio buttons
    ax_radio_site = fig.add_axes(gs[0, 1:], label="radio_site")
    ax_radio_neigh = fig.add_axes(gs[1, 1:], label="radio_neigh")
    ax_radio_metric = fig.add_axes(gs[2, 1:], label="radio_metric")
    ax_cycletime = fig.add_axes(gs[3, 1:], label="cycle_time")

    #Button for cycling Time window
    cycle_time_button = Button(ax_cycletime, label='Cycle Time Window')

    #Radio buttons
    radio_site = RadioButtons(ax_radio_site, SITES)
    radio_area = RadioButtons(ax_radio_neigh, AREAS)
    radio_metric = RadioButtons(ax_radio_metric, ("Listing Frequency", "Price", "Price Regression", "Agg Crime Score", "Avg Sqft"))

    #Set actions for GUI items. 
    # span.on_changed(update_time_span)           #TODO write update_time_span   
    # cycle_time_button.on_clicked(cycle_time)    #TODO write cycle_back
    # radio_site.on_clicked(radio_site_action)    #TODO write radio_site_action
    # radio_area.on_clicked(radio_neigh_action)   #TODO write radio_neigh_action
    # radio_metric.on_clicked(radio_metric_action)#TODO write radio_metric_action

    #TODO initial plot loading here of presets. 


    #Make a custom legend. 
    # legend_elements = [
    #     Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
    #     ]
    # sp_trend.legend(handles=legend_elements, loc='upper left')


    #show the plot!
    plt.show()

def main():
    fp = PurePath(Path.cwd(), Path(f"./data/rental_list.json"))
    global data
    #Load historical data and load into dataframe
    json_f = support.load_historical(fp)
    data = pd.DataFrame.from_dict(json_f, orient="index")
    #Load official neighborhood polygons from data.cityofchicago.org
    # maps = support.load_neigh_polygons()
    graph = load_graph()

if __name__ == "__main__":
    main()