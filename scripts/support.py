from math import sin, cos, sqrt, atan2, radians

def distanceGPS(lat1,lon1,lat2,lon2):
    """
    ##################################################################
    ###     This code calculates the distance (miles) between two points 
    ###     __________________________________________________________
    ###     INPUT:      lat1 - Latitude (degrees) of first object
    ###                 lon1 - Longitude (degrees) of first object
    ###                 lat2 - Latitude (degrees) of second object
    ###                 lon2 - Longitude (degrees) of second object
    ###     OUTPUT:     distance
    ##################################################################
    """
    # approximate radius of earth in miles
    R = 3956 
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a)) #used atan instead of asin
    return(R * c * 0.62137)

# Borrowed from https://github.com/mmachen/housing-search-Chicago/blob/master/project/extra_programs.py
# might adapt this as well. 
# https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python
