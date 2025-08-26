#Import libraries
import numpy as np
from os.path import exists
import support

#Import logger and console from support
from support import logger, log_time, get_time


def sir_plots_alot():
    pass    

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