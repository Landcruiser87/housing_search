import datetime
import numpy as np
import pandas as pd
from sodapy import Socrata
import time
import json
from os.path import exists
from os import get_terminal_size
from shapely.geometry import shape
from shapely.geometry import Polygon
from shapely.ops import unary_union
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
from pathlib import Path, PurePath

################################# Logging Funcs ####################################

################################# Logger functions ####################################
#FUNCTION Logging Futures
def get_file_handler(log_dir:Path)->logging.FileHandler:
    """Assigns the saved file logger format and location to be saved

    Args:
        log_dir (Path): Path to where you want the log saved

    Returns:
        filehandler(handler): This will handle the logger's format and file management
    """	
    log_format = "%(asctime)s|%(levelname)-8s|%(lineno)-4d|%(funcName)-13s|%(message)-108s|" 
                 #f"%(asctime)s - [%(levelname)s] - (%(funcName)s(%(lineno)d)) - %(message)s"
    # current_date = time.strftime("%m_%d_%Y")
    file_handler = logging.FileHandler(log_dir)
    file_handler.setFormatter(logging.Formatter(log_format, "%m-%d-%Y %H:%M:%S"))
    return file_handler

def get_rich_handler(console:Console)-> RichHandler:
    """Assigns the rich format that prints out to your terminal

    Args:
        console (Console): Reference to your terminal

    Returns:
        rh(RichHandler): This will format your terminal output
    """
    rich_format = "|%(funcName)-13s| %(message)s"
    rh = RichHandler(console=console)
    rh.setFormatter(logging.Formatter(rich_format))
    return rh

def get_logger(console:Console, log_dir:Path)->logging.Logger:
    """Loads logger instance.  When given a path and access to the terminal output.  The logger will save a log of all records, as well as print it out to your terminal. Propogate set to False assigns all captured log messages to both handlers.

    Args:
        log_dir (Path): Path you want the logs saved
        console (Console): Reference to your terminal

    Returns:
        logger: Returns custom logger object.  Info level reporting with a file handler and rich handler to properly terminal print
    """	
    #Load logger and set basic level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #Load file handler for how to format the log file.
    file_handler = get_file_handler(log_dir)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    #Don't need to load rich handler in this instance because the TUI will handle all messaging
    # rich_handler = get_rich_handler(console)
    # rich_handler.setLevel(logging.INFO)
    # logger.addHandler(rich_handler)
    logger.propagate = False
    return logger


#FUNCTION get time
def get_time():
    """Function for getting current time

    Returns:
        t_adjusted (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    current_t = datetime.datetime.strptime(current_t_s, "%m-%d-%Y-%H-%M-%S")
    return current_t

########################## Global Variables ##########################################
start_time = get_time().strftime("%m-%d-%Y_%H-%M-%S")
console = Console(color_system="auto", stderr=True)
log_dir = PurePath(Path.cwd(), Path(f'./data/logs/{start_time}.log'))
logger = get_logger(log_dir=log_dir, console=console)
state_dict = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming',
    'DC': 'District of Columbia',
}
#FUNCTION Log time
################################# Timing Func ####################################
def log_time(fn):
    """Decorator timing function.  Accepts any function and returns a logging
    statement with the amount of time it took to run. DJ, I use this code everywhere still.  Thank you bud!

    Args:
        fn (function): Input function you want to time
    """	
    def inner(*args, **kwargs):
        tnow = time.time()
        out = fn(*args, **kwargs)
        te = time.time()
        took = round(te - tnow, 2)
        if took <= 60:
            logging.warning(f"{fn.__name__} ran in {took:.2f}s")
        elif took <= 3600:
            logging.warning(f"{fn.__name__} ran in {(took)/60:.2f}m")		
        else:
            logging.warning(f"{fn.__name__} ran in {(took)/3600:.2f}h")
        return out
    return inner

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

    for Lname in ["total", "homes", "redfin", "realtor", "zillow"]:
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
class CustomEncoder(json.JSONEncoder):
    """Custom numpy JSON Encoder.  Takes in any type from an array and formats it to something that can be JSON serialized. Source Code found here. https://pynative.com/python-serialize-numpy-ndarray-into-json/
    
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
        elif isinstance(obj, pd.DataFrame):
            return obj.to_json(orient='records')
        elif isinstance(obj, dict):
            return obj.__dict__
        elif isinstance(obj, datetime.datetime):
            return datetime.datetime.strftime(obj, "%m-%d-%Y_%H-%M-%S")
        else:
            return super(CustomEncoder, self).default(obj)

#FUNCTION Convert Date
def date_convert(time_big:datetime)->datetime:
    dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
    return dateOb

#FUNCTION Save Data
def save_data(jsond:dict):
    out_json = json.dumps(jsond, indent=2, cls=CustomEncoder)
    with open("./data/rental_list.json", "w") as out_f:
        out_f.write(out_json)

#FUNCTION Load Historical
def load_historical(fp:str)->json:
    if exists(fp):
        with open(fp, "r") as f:
            jsondata = json.loads(f.read())
            return jsondata	

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
