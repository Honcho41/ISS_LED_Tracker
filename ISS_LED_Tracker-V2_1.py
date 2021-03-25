import ephem
import time
import math
from datetime import datetime
import requests
import ISS_Info

import board
import neopixel

# ephem module outputs in radians, variable to convert to degress:
degrees_per_radian = 180.0 / math.pi 

# define a function to set the LED colour when ISS is above my horizon
def issAbove():
    pixels = neopixel.NeoPixel(board.D18, 96, brightness = 0.5)
    pixels.fill((255, 255, 255)) # Bright White

# function to set LED colour when ISS is illuminated by the Sun
def issInDay():
    pixels = neopixel.NeoPixel(board.D18, 96, brightness = 0.5)
    pixels.fill((255, 64, 0)) # burnt orange

# function to set LED colour when ISS is in eclipse
def issInDark():
    pixels = neopixel.NeoPixel(board.D18, 96, brightness = 0.5)
    pixels.fill((5, 0, 25)) # blueish

def issError():
    pixels = neopixel.NeoPixel(board.D18, 96, brightness = 0.5)
    pixels.fill((255, 0, 0)) # red

# function to see if ISS is over observer's horizon
def issOverHorizon():
    # use requests module to extract text file from URL
    try:
        response = requests.get("https://www.celestrak.com/NORAD/elements/stations.txt")
        data = response.text
    except:
        issError()
        print("Do something magic, the internet is broken")
        return True
    
    # use string splitting to extract relevant ISS data.
    # this was done by trial and error and may not be accurate when the TLE updates every few weeks
    iss = ephem.readtle(data[:11],
                        data[20:97],
                        data[97:167])
    
    # set home location using ephem Observer function
    home = ephem.Observer()
    home.lon, home.lat = '-1.78499', '51.56704' # replace these with your longitude (east/west) and latitude (north/south)
    home.elevation = 63 # replace this with your elevation/altitude in meters
    
    # check if ISS is over 10 degrees above horizon
    home.date = datetime.utcnow()
    iss.compute(home)
    altitude = iss.alt * degrees_per_radian
    if altitude > 10:
        return True
    else:
        return False

# function to check is ISS is in daylight
def issDaylight():
    # current ISS latitude and longitude from ISS_info module which outputs as a nested dictionary
    issLong = ISS_Info.iss_current_loc()["iss_position"]["longitude"]
    issLat = ISS_Info.iss_current_loc()["iss_position"]["latitude"]
    
    # set the ISS current location as ephem observer to be used in sunrise/set calcs later
    issCurrent = ephem.Observer()
    issCurrent.lat = issLat
    issCurrent.long = issLong
    issCurrent.elevation = 420000 # at the time of writing ISS averages 420km above surface
    
    # use ephem module to get next sunrise/set times for ISS current location
    next_sunrise_datetime = issCurrent.next_rising(ephem.Sun()).datetime()
    next_sunset_datetime = issCurrent.next_setting(ephem.Sun()).datetime()
    
    # it is day if the next sunset is before the next sunrise
    it_is_day = next_sunset_datetime < next_sunrise_datetime
    
    # if statement to output if ISS is in sunlight or eclipse
    if it_is_day:
        issInDay()
        print(str(datetime.utcnow().strftime('%H:%M:%S')) + " UTC: ISS in daylight")
    else:
        issInDark()
        print(str(datetime.utcnow().strftime('%H:%M:%S')) + " UTC: ISS in dark")

# run the functions through an infinite while loop
while True:
    if issOverHorizon():
        issAbove()
        print(str(datetime.utcnow().strftime('%H:%M:%S')) + " UTC: ISS currently visible")
    else:
        issDaylight()
    time.sleep(30)
