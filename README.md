<h1 align="center">
  <b> Chicago Housing Search Tool </b><br>
</h1>

This repo is meant to coalesce different housing resources to aide in searching for housing in Chicago.  The aim is to build a dataset of available housing in chicago, then search hourly for new listings.  If a new listing is found, a text is sent to myself via sms gateway to look at the listing.  Also going to build email functionality as my girlfriend doesn't want to get hammered with texts.  

### Requirements
- Python >= 3.8


### Required Libraries
- Found in the requirements.txt file
- ipykernel installs a bunch of crap for me to use with python interative in VSCode.  
- Basic libraries are:
  - Numpy
  - Pandas
  - requests
  - BeautifulSoup - (I know i know.  But its the best way to parse html)
    -No available json data for any of the housing sites so I had to use the soups. 

### Sites to search
- [] - [Zillow.com](https://www.zillow.com)
- [] - [craigslist.com](https://www.craiglist.org)
- [] - [rent.com](https://www.rent.com)

### External Data Sources
- [CTA L stops](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme/data)
- [CTA Crime data](https://data.cityofchicago.org/Public-Safety/Gun-Crimes-Heat-Map/iinq-m3rg)
- 