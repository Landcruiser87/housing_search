import datetime
import numpy as np
import pandas as pd
from sodapy import Socrata
import time
import json
from os.path import exists
from os import get_terminal_size
from shapely.geometry import shape
import geodatasets
import logging

#Progress bar fun
from rich.progress import (
    Progress,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.logging import RichHandler
from rich.align import Align
from rich.layout import Layout
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from geopy import Nominatim, ArcGIS
import geopandas as gpd
from pathlib import Path

console = Console(color_system="truecolor")

################################# Logging Funcs ####################################

def get_file_handler(log_dir:Path)->logging.FileHandler:
    """Assigns the saved file logger format and location to be saved

    Args:
        log_dir (Path): Path to where you want the log saved

    Returns:
        filehandler(handler): This will handle the logger's format and file management
    """	
    LOG_FORMAT = "%(asctime)s|%(levelname)-8s|%(lineno)-3d|%(funcName)-14s|%(message)s|" 
    current_date = time.strftime("%m-%d-%Y_%H-%M-%S")
    log_file = log_dir / f"{current_date}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, "%m-%d-%Y %H:%M:%S"))
    return file_handler

def get_rich_handler(console:Console):
    """Assigns the rich format that prints out to your terminal

    Args:
        console (Console): Reference to your terminal

    Returns:
        rh(RichHandler): This will format your terminal output
    """
    FORMAT_RICH = "| %(levelname)-8s | %(funcName)-12s |%(message)s "#%(levelname)-8s | %(lineno)-3d
    rh = RichHandler(level=logging.INFO, console=console)
    rh.setFormatter(logging.Formatter(FORMAT_RICH))
    return rh

def get_logger(log_dir:Path, console:Console)->logging.Logger:
    """Loads logger instance.  When given a path and access to the terminal output.  The logger will save a log of all records, as well as print it out to your terminal. Propogate set to False assigns all captured log messages to both handlers.

    Args:
        log_dir (Path): Path you want the logs saved
        console (Console): Reference to your terminal

    Returns:
        logger: Returns custom logger object.  Info level reporting with a file handler and rich handler to properly terminal print
    """	
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_file_handler(log_dir)) 
    # logger.addHandler(get_rich_handler(console))  #Was causing flickering error in the rendering because the log statments kept trying to print
    logger.propagate = False
    return logger

################################# Rich Functions ####################################

class MakeHeader:
    """Display header with clock."""

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[b]Housing[/b] Search Application",
            datetime.datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        return Panel(grid, style="green on black")

class MainTableHandler(logging.Handler):
    """Custom logging handler that saves off every entry of a logger to a temporary
    list.  As the size of the list grows to be more than half the terminal
    height, it will pop off the first item in the list and redraw the
    main_table. 

    Args:
        logging (Handler): modified logging handler. 
    """	
    def __init__(self, main_table: Table, layout: Layout, log_level: str):
        super().__init__()
        self.main_table = main_table
        self.log_list = []
        self.layout = layout
        self.log_format = "|%(levelname)-8s | %(funcName)-12s |%(message)s "
        self.setLevel(log_level)

    def emit(self, record):
        record.asctime = record.asctime.split(",")[0]
        #msg = self.format(record) #if you want just the message info switch comment lines
        msg = self.log_format % record.__dict__
        tsize = get_terminal_size().lines // 2
        if len(self.log_list) > tsize:
            self.log_list.append(msg)
            self.log_list.pop(0)
            self.main_table = redraw_main_table(self.log_list)
            self.layout["termoutput"].update(Panel(self.main_table, border_style="green"))
        else:
            self.main_table.add_row(msg)
            self.log_list.append(msg)

#FUNCTION make main table
def make_main_table():
    main_table = Table(
        expand=True,
        show_header=False,
        header_style="bold",
        title="[blue][b]Log Entries[/b]",
        highlight=True,
    )
    main_table.add_column("Log Output")
    return main_table

#FUNCTION make rich display
def make_rich_display(totalstops:int):
    layout = make_layout()
    main_table = make_main_table()
    totalprog, task = overalprog(totalstops, "Program progress")
    sleeper = sleepspinner()

    layout["header"].update(MakeHeader())
    layout["termoutput"].update(Panel(main_table, border_style="blue"))
    layout["overall_prog"].update(
        Panel(
            Align.center(
                totalprog,
                vertical="middle", 
                height=6),
            border_style="green",
            title="Overall Progress",
            title_align="center",
            expand=True
        )
    )
    layout["sleep_prog"].update(
        Panel(
            Align.center(
                totalprog,
                vertical="middle", 
                height=6),
            border_style="red",
            title="sleepytimer",
            title_align="center",
            expand=True
        )
    )

    for Lname in ["total", "apartments", "craigs", "homes", "redfin", "realtor", "zillow"]:
        layout[Lname].update(
            Panel(
                Align.center(Text("0"), vertical="middle"),
            title=f"{Lname}",
            title_align="center",
            border_style="red")
        )
    return layout, totalprog, task, main_table

def make_layout() -> Layout:
    """Creates the rich Display Layout

    Returns:
        Layout: rich Layout object
    """
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3), 
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(name="termoutput",), 
        Layout(name="progs"),
    )
    layout["progs"].split_column(
        Layout(name="overall_prog"), 
        Layout(name="sleep_prog"),
        Layout(name="find_count")
    )
    layout["find_count"].split_row(
        Layout(name="total"),
        Layout(name="apartments"),
        Layout(name="craigs"),
        Layout(name="homes"),
        Layout(name="realtor"),
        Layout(name="redfin"),
        Layout(name="zillow")
    )
    return layout

def update_count(newdigs:int, layout:Layout, Lname:str):
    current = int(layout[Lname].renderable.renderable.renderable.plain)
    current += newdigs
    format_p = Panel(
        Align.center(Text(f"{current}"), vertical="middle"),
        title=f"{Lname}",
        title_align="center",
        border_style="green")

    return format_p

def update_border(layout:Layout, Lname:str):
    current = int(layout[Lname].renderable.renderable.renderable.plain[0])
    format_p = Panel(
        Align.center(Text(f"{current}"), vertical="middle"),
        title=f"{Lname}",
        title_align="center",
        border_style="magenta")

    return format_p

def redraw_main_table(temp_list: list) -> Table:
    """Function that redraws the main table once the log
    entries reach a certain legnth.

    Args:
        temp_list (list): Stores the last 10 log entries

    Returns:
        Table: rich Table object
    """	
    main_table = Table(
        expand=True,
        show_header=False,
        header_style="bold",
        title="[blue][b]Log Entries[/b]",
        highlight=True,
    )
    main_table.add_column("Log Entries")
    for row in temp_list:
        main_table.add_row(row)

    return main_table


################################# Rich Spinners ####################################
#FUNCTION sleep progbar
def sleepspinner():
    my_progress_bar = Progress(
        TextColumn("{task.description}"),
        SpinnerColumn("pong"),
        BarColumn(),
        TextColumn("*"),
        "time remain:",
        TextColumn("*"),
        TimeRemainingColumn(),
        TextColumn("*"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
        refresh_per_second=10
    )
    return my_progress_bar

#FUNCTION sleep progbar run function
def run_sleep(naps:int, msg:str, layout):
    spinner = sleepspinner()
    layout["sleep_prog"].update(
        Panel(
            Align.center(
                spinner,
                vertical="middle", 
                height=6),
            border_style="green",
            title="sleepytimer",
            title_align="center",
            expand=True)
            )
    # Maybe load this into the layout and then have it disappear?
    task = spinner.add_task(msg, total=naps)
    for nap in range(naps):
        time.sleep(1)
        spinner.advance(task)
    
    layout["sleep_prog"].update(
        Align.center(
            Panel("awaits next nap... :zzz: ", border_style="red", expand=True), 
            vertical="middle", 
            height=6)
            )
            
#FUNCTION  overall progbar
def overalprog(stops:int, msg:str):
    my_progress_bar = Progress(
        TextColumn("{task.description}"),
        SpinnerColumn("pong"),
        BarColumn(),
        TextColumn("*"),
        "time elapsed:",
        TextColumn("*"),
        TimeElapsedColumn(),
        TextColumn("*"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        refresh_per_second=10,
    )

    task = my_progress_bar.add_task(msg, total=stops)
    return my_progress_bar, task

#CLASS Numpy encoder
class NumpyArrayEncoder(json.JSONEncoder):
    """Custom numpy JSON Encoder.  Takes in any type from an array and formats it to something that can be JSON serialized.
    Source Code found here.  https://pynative.com/python-serialize-numpy-ndarray-into-json/
    Args:
        json (object): Json serialized format
    """	
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyArrayEncoder, self).default(obj)

#FUNCTION Convert Date
def date_convert(time_big:datetime)->datetime:
    dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
    return dateOb

#FUNCTION Save Data
def save_data(jsond:dict):
    out_json = json.dumps(jsond, indent=2, cls=NumpyArrayEncoder)
    with open("./data/rental_list.json", "w") as out_f:
        out_f.write(out_json)

#FUNCTION Load Historical
def load_historical(fp:str)->json:
    if exists(fp):
        with open(fp, "r") as f:
            jsondata = json.loads(f.read())
            return jsondata	

#FUNCTION Closest L
def closest_L_stop(data:list)->list:
    #Load up Lstop data
    stops = pd.read_csv(
        "./data/CTA_Lstops.csv",
        header=0,
        index_col="STOP_ID"
    )
    for listing in data:
        if listing.lat and listing.long:
            lat1 = listing.lat
            lon1 = listing.long

            min_dist = 20000
            for stop in stops.index:
                lat2, lon2 = stops.loc[stop, "Location"].strip("()").split(",")
                lat2, lon2 = float(lat2), float(lon2)
                dist = haversine_distance(lat1, lon1, lat2, lon2)
                if dist <= min_dist:
                    min_dist = dist
                    station = stops.loc[stop, "STATION_NAME"]
            listing.L_dist = (station, round(min_dist, 2))

    return data

#FUNCTION Get Lat Long
def get_lat_long(data:list, citystate:tuple, logger:logging.Logger, layout)->list:
    noma_params = {
        "user_agent":"myApp",
        "timeout":5,
    }
    geolocator = Nominatim(**noma_params)
    # arc_params = {
    # 	"exactly_one":True,
    # 	"timeout":10,
    # }
    # backupgeo = ArcGIS()

    #TODO.  Add backup geocoder?  Going with ARCGis
        #ArcGIS has up to 20k free geocode requests a month.  That should be plenty
    
    for listing in data:
        
        #Early termination to the loop if lat/long already exist
        if isinstance(listing.lat, float) and isinstance(listing.long, float):
            continue
        #Or if the listing doesn't have an address????  Come on people.
        if not listing.address:
            continue

        run_sleep(np.random.randint(2, 6), "ohhh GPS sleepys", layout)
        address = listing.address
        logger.info(f"searching GPS for {address}")
        #If city and state aren't present, add them
        if citystate[0].lower() not in address.lower():
            listing.address = address + " " + citystate[0]
        if citystate[1].lower() not in address.lower():
            listing.address = address + " " + citystate[1]

        srch_add = listing.address + " USA"
        #First search Novatim
        try:
            location = geolocator.geocode(srch_add)
        except Exception as error:
            logger.warning(f"an error occured in Nominatim\n{error}")
            location = None

        #If a location is found, assign lat long
        if location:
            lat, long = location.latitude, location.longitude
            listing.lat = lat
            listing.long = long

        #If that fails, search ARCgis
        # locatedos = backupgeo(srch_add)
        # if locatedos:
        # 	lat, long = location.latitude, location.longitude
        # 	listing.lat = lat
        # 	listing.long = long

    return data


#FUNCTION Bounding box
def in_bounding_box(bounding_box:list, lat:float, lon:float)->bool:
    """[Given two corners of a box on a map.  Determine if a point is
     within said box.  Step 1.  You cut a hole in that box.]

    Args:
        bounding_box (list): [list of GPS coordinates of the box]
        lat (float): [lattitude of point]
        lon (float): [longitude of point]

    Returns:
        (bool): [Whether or not is within the given GPS ranges 
        in the bounding box]
    """		
    bb_lat_low = bounding_box[0]
    bb_lat_up = bounding_box[2]
    bb_lon_low = bounding_box[1]
    bb_lon_up = bounding_box[3]

    if bb_lat_low < lat < bb_lat_up:
        if bb_lon_low < lon < bb_lon_up:
            return True

    return False

#FUNCTION Haversine
def haversine_distance(lat1:float, lon1:float, lat2:float, lon2:float)->float:
    """[Uses the haversine formula to calculate the distance between 
    two points on a sphere]

    Args:
        lat1 (float): [latitude of first point]
        lon1 (float): [longitude of first point]
        lat2 (float): [latitude of second point]
        lon2 (float): [latitue of second point]

    Returns:
        dist (float): [Distance between two GPS points in miles]

    Source:https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python
    """	
    from math import radians, cos, sin, asin, sqrt
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 3956 # Radius of earth in miles. Use 6371 for kilometers
    return c * r

#FUNCTION URL Format
def urlformat(urls:list)->str:
    """This formats each of the list items into an html list for easy ingestion into the email server

    Args:
        urls (list): List of new listings found

    Returns:
        str: HTML formatted string for emailing
    """	
    
    links_html = "<ol>"
    if len(urls) > 1:
        for link, site, neigh in urls:
            links_html += f"<li><a href='{link}'> {site} - {neigh} </a></li>"
    else:
        links_html = f"<li><a href='{urls[0][0]}'> {urls[0][1]} - {urls[0][2]} </a></li>"
    links_html = links_html + "</ol>"
    return links_html

#FUNCTION Send Housing Email
def send_housing_email(urls:str):
    """[Function for sending an email.  Formats the url list into a basic email with said list]

    Args:
        url (str): [url of the listing]

    Returns:
        [None]: [Just sends the email.  Doesn't return anything]
    """	
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    def inputdatlink(urls:str):
        html = """
        <html>
            <body>
                <p>Helloooooooooo!<br>
                You have new houses to look at!<br>
                """ + urls + """
                </p>
            </body>
        </html>
        """
        return html

    with open('./secret/login.txt') as login_file:
        login = login_file.read().splitlines()
        sender_email = login[0].split(':')[1]
        password = login[1].split(':')[1]
        receiver_email = login[2].split(':')[1].split(",")
        
    # Establish a secure session with gmail's outgoing SMTP server using your gmail account
    smtp_server = "smtp.gmail.com"
    port = 465

    html = inputdatlink(urls)

    message = MIMEMultipart("alternative")
    message["Subject"] = "New Housing Found!"
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_email)   #message[To] needs to be a str, 
                                                #but sendmail wants it as a list????  OOOK
                                                #receiver email is a list due to the split method
    attachment = MIMEText(html, "html")
    message.attach(attachment)
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)		
        server.sendmail(sender_email, receiver_email, message.as_string())

#FUNCTION Load neighborhood boundaries
def socrata_api(update:bool=False):
                
    def load_shape_objects(polygon:str):
        # polygon = polygon.replace("'", "\"")
        # geo_data = json.loads(polygon)
        return shape(polygon)
    
    if update:
        with open('./secret/chicagodata.txt') as login_file:
            login = login_file.read().splitlines()
            app_token = login[0].split(':')[1]
            
        client = Socrata("data.cityofchicago.org", app_token)
        datasets = {
            "map"   :{"id":"y6yq-dbs2"},
            "health":{"id":"iqnk-2tcu"},
            "zip"   :{"id":"unjd-c2ca"},
            "pop"   :{"id":"85cm-7uqa"},
            "city"  :{"id":"qqq8-j68g"}
        }
        merged_df = None
        for db_name in datasets.keys():
            try:
                #Grab neighborhood coords
                results = client.get(
                    datasets[db_name]["id"],
                    limit=5000
                )
                df = pd.DataFrame.from_records(results)
                if "the_geom" in df.columns.tolist():
                    # df["the_geom"] = df["the_geom"].astype(str)
                    df["the_geom"] = df["the_geom"].apply(load_shape_objects)
                    df = gpd.GeoDataFrame(df, geometry="the_geom")

                datasets[db_name] = df.copy()
                # df.to_csv(f"./data/chicago_{db_name}.csv", sep=",", index=False)

            except Exception as e:
                raise e
        
        #Manual data cleaning
        chicago = gpd.read_file(geodatasets.get_path("geoda.chicago_commpop"))
        datasets["chicago"] = chicago
        datasets["chicago"]["community"] = datasets["chicago"]["community"].apply(lambda x:x.lower().replace("montclare", "montclaire"))
        datasets["health"]["community_area_name"] = datasets["health"]["community_area_name"].apply(lambda x:x.lower().replace("o'hare", "ohare"))
        datasets["map"]["pri_neigh"] = datasets["map"]["pri_neigh"].apply(lambda x:x.lower().replace("o'hare", "ohare"))
        datasets["map"]["sec_neigh"] = datasets["map"]["sec_neigh"].apply(lambda x:x.lower())
        
        #quick check
        #[f"{x:_<21} {y}" for x, y in list(zip(datasets["map"]["pri_neigh"],datasets["map"]["sec_neigh"]))]
        #rename columns and map city polygon to 
        datasets["health"].rename(columns={"community_area_name":"community"}, inplace=True)
        datasets["map"].rename(columns={"pri_neigh":"community"}, inplace=True)
        datasets["pop"].rename(columns={"geography":"zip"}, inplace=True)

        #Two boundaries in the zip database have expanded and are stored as different records.  
        #We need to manually combine the polygons, shape_area, and shape length, while keeping the original id. #not sure if that will hose us later. 

        for area in ["60707", "60643"]:
            rows = datasets["zip"][datasets["zip"]["zip"]==area]
            for col in ["the_geom", "shape_area", "shape_len"]:
                if col == "the_geom":
                    bigpoly = rows.iloc[0, 0]
                    lilpoly = rows.iloc[1, 0]
                    datasets["zip"].iloc[rows.index[0], 0] = gpd.overlay(df1=bigpoly, df2=lilpoly, how="union")
                else:
                    datasets["zip"][datasets["zip"].index == rows[0].index][col] = rows[col] 

        #first merge chicago and health. then with maps.  
        #Then update their polygons only keeping the ones that have data. 
        merged_neigh = datasets["chicago"].merge(datasets["health"], on="community", how="outer")
        merged_neigh = merged_neigh.merge(datasets["map"], on="community", how="left")
        merged_zip = datasets["pop"].merge(datasets["zip"], on="zip", how="left", validate="m:m")
        cityrows = merged_zip.loc[:, "zip"] == "Chicago"
        merged_zip.loc[cityrows, "the_geom"] = datasets["city"].loc[:, "the_geom"]
        merged_zip.loc[cityrows, "shape_area"] = datasets["city"].loc[:, "shape_area"]
        merged_zip.loc[cityrows, "shape_len"] = datasets["city"].loc[:, "shape_len"]
        merged_zip.loc[cityrows, "objectid"] = 0
        #zipcode based datasets
            #pop
            #zip
                #Note. Getting 4 more rows than expected and not sure why.  
                #Wierd, it two random zip codes??  oooooook
                # 60707, 60643
        #neighborhoodbased datasets
            #health
            #chicago
            #map

        #Convert the shp files to usable Shapely objects
        for db_name in datasets.keys():
            #Merge the dataset
            if "shape_area" in datasets[db_name].columns.tolist():
                merged_df = gpd.sjoin(merged_df, datasets[db_name], on="shape_area", how="inner")
                # merged_df = pd.merge(merged_df, datasets[db_name], on=["the_geom"], how="outer") 
                # merged_df.drop("the_geom_x", axis=1, inplace=True)
            else:
                pass

        merged_df["the_geom"] = merged_df["the_geom"].apply(load_shape_objects)

        return merged_df
    
    else:
        fp = f"./data/chicago_merged.csv"
        return gpd.read_file(fp)
    #IDEA
    #towed vehicles = ygr5-vcbg
    #police stations = gkur-vufi
    #fire stations = hp65-bcxv
    #population = 85cm-7uqa
    #?  Could aggregate live crime data for each neighborhood too for the last year.  That would be awesome!

    #BUG
    #NOTES
    #Main problem, is i've got different shapes for different key values.  
    #zipcodes
    #population data by zip
    #neighborhoods
    #neighborhood health 
    #a chicago pop dataset/shapes from geodatasets
        #How in the f do i merge them all to be usable????
    #I have all the polygons for zip and neighborhoods... 
        #maybe make a switch between them?  would be kinda cool.  
        #



#FUNCTION Crime Scoring
def crime_score(data:list, logger:logging.Logger, layout) -> list:
    """[Connects to data.cityofchicago.org and pulls down all the 
    crime data for the last year, in a 1 mile radius.  It then recategorizes
    the crimes into scores based on the percentage of total crime in that area.]

    Args:
        data (list): List of PropertyInfo dataclasses
    Raises:
        ValueError: [Check to make sure we got a years worth of data]

    Returns:
        list: [List of Property Info dataclasses with updated crime scores]
    """	
    with open('./secret/chicagodata.txt') as login_file:
        login = login_file.read().splitlines()
        app_token = login[0].split(':')[1]
        
    client = Socrata("data.cityofchicago.org", app_token)

    #Search radius is 0.91 miles
    #Sets lookback to 1 year from today
    ze_date = str(datetime.datetime.today().date() - datetime.timedelta(days=365))
    c_dtypes = [
        ("id"          ,str, 60),
        ("date"        ,datetime.datetime),
        ("iucr"        ,str, 60),
        ("fbi_code"    ,str, 60),
        ("latitude"    ,float),
        ("longitude"   ,float),
        ("primary_type",str, 240),
        ("description" ,str, 600),
        ("arrest"      ,str, 20),
        ("domestic"    ,str, 20),
    ]

    for listing in data:
        lat1 = listing.lat
        lon1 = listing.long

        if lat1 and lon1:
            try:
                # If the listing has a lat / long, search the area within a 1 mile radius, over the past 365 days.  Pull back the select fields for analysis
                results = client.get("ijzp-q8t2",
                    select="id, date, iucr, fbi_code, latitude, longitude, primary_type, description, arrest, domestic",
                    where=f"latitude > {lat1-0.1} AND latitude < {lat1+0.1} AND longitude > {lon1-0.1} AND longitude < {lon1+0.1} AND date > '{ze_date}'",
                    limit=800000
                )
                run_sleep(np.random.randint(2, 6), "BE NICE to your sister", layout)

            except Exception as e:
                logger.warning(e)
                continue          


            #NOTES
                #IDEA -Redo Scoring
                #I'd like to redo the crime scoring section becuase I think there's alot more valuable data there than previously
                #found.  I need a way to classify risk in a region.  Which is no easy task.  
                    #Ideas for crime severity
                     #1. Using arrest/domestic as simple scaling of importance
                      #2. Make another requeset and use the IUCR codes
                           #I'm betting this will be the better route though as
                         #there will be a felony misdemeanor charge dilineation in there. 
                    #So primary type and description are the results of the IUCR codes. Makes sense.
                     #Don't really need to pull them but I could use the logic of how their structured. 
                      #Looks like there's 5 different pages dilineated by crimes in the 1000's
                       #page 1 is most frequent, 
                    #page 2 is burglary and prostitution?  Wierd
                     #page 3 is Narcotics.  Lots of different charges here. 
                      #page 4 is other offenses.
       
                   #IDEA What about a week by week analysis up to a year back for each primary_type
                       #?Month might be easier storage.
                       #That could give a sense of seasonality and trend for important categories
                    #Multi line chart with regressions? in that radius over the past year. 
                         #This will be cool ^^^^^
                    #Store those as an array for easy graphing and would be minimal data overhead if grouped by week instead,
                         #NOTE -json storage.
                            #If you want to save an array inside json.  we'll store it on the 3rd level of the dic so its 
                               #format will look like {"array":[1,2,3,4,5,6]}
                              #https://pynative.com/python-serialize-numpy-ndarray-into-json/
                              #That way it won't indent the json at that level and make the json row count go bonkers
                             #Maybe store the top 10 to 15?.  That should keep the dataset size fairly small
                           #Score the scoring dict too, buy we'll still need to update that. 

            if results:
                #Set up array
                crime_arr = np.zeros(shape=(len(results)), dtype=c_dtypes)
                #Fill it in row by row
                for idx, res in enumerate(results):
                    crime_arr[idx] = tuple(res.values())
                
                #Convert to datetimes
                func = np.vectorize(lambda x: date_convert(x))
                crime_arr["date"] = np.apply_along_axis(func, 0, crime_arr["date"])
                
                #Check the last dates record.  If its not within the last year, 
                #make another request until we hit that date. 
                    # Don't forget to filter any data that may come in extra. 
                date_check = crime_arr["date"].min()
                if date_check > datetime.datetime.today() - datetime.timedelta(days=365):
                    #Need to figure out how to remake the request if i hit the 800k limit. 
                    raise ValueError('Yo Query needeth be BIGGER')

                #Checking memory consumption
                #sum(crime_df.memory_usage(deep=True) / 1_000_000)
                #Req 500k records costs you about 21.7 MB

                total_crimes = crime_arr.shape[0]

                scores = {
                    'drug_score':0,
                    'gun_score':0,
                    'murder_score':0,
                    'perv_score':0,
                    'theft_score':0,
                    'violence_score':0,
                    'property_d_score':0
                }

                narcotics = set(['NARCOTICS', 'OTHER NARCOTIC VIOLATION'])
                guns = set(['WEAPONS VIOLATION', 'CONCEALED CARRY LICENSE VIOLATION'])
                guns_sub = set(['HANDGUN', 'ARMOR', 'GUN', 'FIREARM', 'AMMO', 'AMMUNITION', 'RIFLE'])
                murder = set(['HOMICIDE'])
                theft = set(['BURGLARY', 'ROBBERY', 'MOTOR VEHICLE THEFT', 'THEFT', 'DECEPTIVE PRACTICE','GAMBLING'])
                sex_crimes = set(['CRIMINAL SEXUAL ASSAULT', 'SEX OFFENSE',  'PROSTITUTION', 'STALKING', 'PUBLIC INDECENCY'])
                sex_crimes_sub = set(['PEEPING TOM', 'SEXUAL', 'SEX OFFENDER'])
                human_violence = set(['BATTERY', 'ASSAULT', 'OFFENSE INVOLVING CHILDREN', 'INTIMIDATION', 'KIDNAPPING', 'HUMAN TRAFFICKING','INTERFERENCE WITH PUBLIC OFFICER', 'OBSCENITY', 'PUBLIC PEACE VIOLATION'])
                human_v_kids = set(['CHILDREN'])
                property_damage = set(["ARSON","CRIMINAL DAMAGE", 'CRIMINAL TRESPASS'])
                property_d_sub = set(['CRIMINAL DAMAGE'])

                for idx in range(total_crimes):
                    #Primary categorization
                    crime = crime_arr[idx]['primary_type']
                    if " " in crime:
                        crimeset = set(crime.split())
                    else:
                        crimeset = set([crime])
                    
                    if " " in crime_arr[idx]['description']:
                        crime_sub_set = set(crime_arr[idx]['description'].split())
                    else:
                        crime_sub_set = set([crime_arr[idx]['description']])

                    #Drugs
                    if crimeset & narcotics:
                        scores['drug_score'] += 1

                    #Guns
                    if crimeset & guns:
                        scores['gun_score'] += 1
            
                    #Gun description subsearch if primary_type doesn't catch it.
                    elif crime_sub_set & guns_sub:
                        scores['gun_score'] += 1
                    
                    #Murder
                    if crimeset & murder:
                        scores['murder_score'] += 10
                    
                    #Theft
                    if crimeset & theft:
                        scores['theft_score'] += 1

                    #Sexual Crimes
                    if crimeset & sex_crimes:
                        scores['perv_score'] += 2

                    #Sex Crimes subsearch
                    elif crime_sub_set & sex_crimes_sub:
                        scores['perv_score'] += 2

                    #humanViolence
                    if crimeset & human_violence:
                        scores['violence_score'] += 1

                    #humanviolence subsearch
                    elif crime_sub_set & human_v_kids:
                        scores['violence_score'] += 5
                    
                    #property damage 
                    if crimeset & property_damage:
                        scores['property_d_score'] += 1

                    #property damage subsearch
                    elif crimeset & property_d_sub:
                        scores['property_d_score'] += 1
                    
                scores = {k:round((v/total_crimes )*100, 2) for k, v in scores.items()}
                listing.crime_sc = scores
                del results
    return data

#TODO - Add DC crime module
    # https://datagate.dc.gov/search/open/crimes?daterange=1year%20to%20date&details=true&format=csv
    
#TODO - Add DC closest train option

#https://kplauritzen.dk/2021/08/11/convert-dataclasss-np-array.html
#TODO - Look at above link
    #might be an easier way to offload np arrays from a dataclass

# def __array__(self):
# 	return np.array(astuple(self))
# def __len__(self):
# 	return astuple(self).__len__()
# def __getitem__(self, item):
# 	return astuple(self).__getitem__(item)
