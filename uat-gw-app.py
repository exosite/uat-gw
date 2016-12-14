import requests
import time
import json
import urlparse
import struct
from dotstar import Adafruit_DotStar

from GatewayEngine import utils

import os
import glob
import time
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f


numpixels = 20 # Number of LEDs in strip

# Here's how to control the strip from any two GPIO pins:
datapin   = 23
clockpin  = 24
strip     = Adafruit_DotStar(numpixels, order='bgr')


def getTemperature():
    # Read the temperature of the temp sensor
    # in fahrenheit
    return read_temp()[1]


def setLedColor(hexcolor):
    # Hex color in string format (e.g`ff0012`)

    try:
        hexcolor = int(hexcolor,16)
    except:
        print('Color is not valid hex')
        return

    if hexcolor < 0 or hexcolor > 0xffffff:
        print('invalid color')
        return

    # Set color of all leds
    for i in range(numpixels):
        strip.setPixelColor(i, hexcolor)

def ledsOff():
    for i in range(numpixels):
        strip.setPixelColor(i,0)


def main():
    # init the light strip
    strip.begin()
    strip.setBrightness(64)

    # wait to get cik from GWE
    print("waiting on cik")
    while utils.gwe_cik() == "":
        time.sleep(1)

    print("Got cik: " + utils.gwe_cik())

    while True:
        t = getTemperature()
        print("Got temperature of: " + str(t))

        payload = 'raw_data={"temperature":' + str(t) + "{"

        # write values and read state
        headers = {"X-Exosite-CIK": utils.gwe_cik(), "Content-Type":"application/x-www-form-urlencoded; charset=utf-8", "Accept":"application/x-www-form-urlencoded; charset=utf-8"}
        res = requests.post('https://m2.exosite.com/onep:v1/stack/alias?state', data = payload, headers=headers)
        print(res)
        body = res.text
        print(body)
        statestring = urlparse.parse_qs(body)['state'][0]
        stateDict = json.loads(statestring)
        print(stateDict)
        color = stateDict.get('led_color')
        if color != None:
            a = color.strip('#')
            setLedColor(a)

        power = stateDict.get('led_power')
        if power != None:
            strip.setLedPower(power)

        state = stateDict.get('led_state')
        if state == False or state == 0:
            ledsOff()

        strip.show()
        time.sleep(3)



if __name__ == "__main__":
    main()

