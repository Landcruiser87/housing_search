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
    valid_sect = hs_data['section_info']['valid']
    global ax_map, gs, fig
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[6, 1])
    plt.subplots_adjust(hspace=0.40)
    ax_map = fig.add_subplot(gs[0, :2], label="mainplot")
    first_sect = np.where(hs_data['section_info']['valid']!=0)[0][0]
    start_w = hs_data['section_info'][first_sect]['start_point']
    end_w = hs_data['section_info'][first_sect]['end_point']
    ax_map.plot(range(start_w, end_w), wave[start_w:end_w], color='dodgerblue', label='mainECG')
    ax_map.set_xlim(start_w, end_w)
    ax_map.set_ylabel('Voltage (mV)')
    ax_map.set_xlabel('ECG index')
    ax_map.legend(loc='upper left')

    #brokebarH plot for the background of the slider. 
    ax_section = fig.add_subplot(gs[1, :2])
    ax_section.broken_barh(valid_grouper(valid_sect), (0,1), facecolors=('tab:blue'))
    ax_section.set_ylim(0, 1)
    ax_section.set_xlim(0, valid_sect.shape[0])

    sect_slider = Slider(ax_section, 
        label='Sections',
        valmin=first_sect, 
        valmax=len(valid_sect), 
        valinit=first_sect, 
        valstep=1
    )

    #Invalid step axes placeholders
    axnext = plt.axes([0.595, 0.01, 0.15, 0.050])
    axprev = plt.axes([0.44, 0.01, 0.15, 0.050])

    #Singlestep axes placholders
    ax_sing_next = plt.axes([0.28, 0.01, 0.15, 0.050])
    ax_sing_prev = plt.axes([0.125, 0.01, 0.15, 0.050])

    #Jump section axes placeholders
    ax_jump_textb = plt.axes([0.88, 0.01, 0.06, 0.050])

    #Add axis container for radio buttons
    ax_radio = plt.axes([0.905, .45, 0.09, 0.20])

    #Button for Invalid Step process
    next_button = Button(axnext, label='Next Invalid Section')
    prev_button = Button(axprev, label='Previous Invalid Section')

    #Button for single step process
    sing_next_button = Button(ax_sing_next, label='Single Step Forward')
    sing_prev_button = Button(ax_sing_prev, label='Single Step Backward')

    #TextBox for section jump
    jump_sect_text = TextBox(ax_jump_textb, 
        label='Jump to Section',
        textalignment="center", 
        hovercolor='green'
    )

    #Radio buttons
    radio = RadioButtons(ax_radio, ('Price Trend','Safety Rating' 'Availability'))

    #Set actions for GUI items. 
    sect_slider.on_changed(update_plot)
    next_button.on_clicked(move_slider_forward)
    prev_button.on_clicked(move_slider_back)
    sing_next_button.on_clicked(move_slider_sing_forward)
    sing_prev_button.on_clicked(move_slider_sing_back)
    radio.on_clicked(radiob_action)
    jump_sect_text.on_submit(jump_slider_to_sect)

    #Make a custom legend. 
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=val[0], markerfacecolor=val[1], markersize=10) for val in PEAKDICT.values()
        ]
    ax_map.legend(handles=legend_elements, loc='upper left')
    plt.show()

def main():
    fp = PurePath(Path.cwd(), Path(f"./data/rental_list.json"))
    global data
    #Load historical data and load into dataframe
    json_f = support.load_historical(fp)
    data = pd.DataFrame.from_dict(json_f, orient="index")
    #Load official neighborhood polygons from data.cityofchicago.org
    maps = support.load_neigh_polygons()
    #
    graph = "load_graph()"

if __name__ == "__main__":
    main()