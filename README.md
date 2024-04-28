<h1 align="center">
  <b> Housing Search Tool </b><br>
</h1>

This repo is meant to coalesce different housing resources to aide in searching for housing in Chicago.  The aim is to build a dataset of available housing in chicago, then search hourly for new listings.  If a new listing is found, an email is sent to the user. 
Datasets are kept in the data folder.


### Base Python Requirements
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

### Other Requirements
- In order to use the email functionality, you need to create a dummy account on gmail. 
- Once you do, authorize it for 2step authentication. 
- Generate an App password for the account
- Store credentials in a text file under a `/secret` folder you'll need to create.
  
### Workflow - Rewrite
1. Main file will run indivdiual sub scripts for each source.  (Makes failure tracing easier)
2. For each source, pull off relevant info for each listing.  
   - Makes sure to use info that's common to all sources. 
   - Store any extra data you find in a text field for cos sim probably
   - Craigs is the only one you have to load each individual link. As not all their 
     information is stored on the front page.
3. After each site / neighborhood retrieval.  Score the listings for these traits
   - Closest L Stop
   - Crime score
4. Send support email with any new links that aren't saved already. 
   

### Sites to search
- [x] - [craigslist](https://www.craiglist.org)
- [x] - [zillow](https://www.zillow.com)
- [x] - [rent.com](https://www.rent.com)
- [x] - [apartments.com](https://www.apartments.com)
- [ ] - [redfin](https://www.redfin.com)

### External Data Sources
- [CTA L stops](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme/data)
- [CTA Crime data](https://data.cityofchicago.org/Public-Safety/Gun-Crimes-Heat-Map/iinq-m3rg)