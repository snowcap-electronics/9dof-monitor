# -*- coding: utf-8 -*-

#  Copyright 2014 Tuomas Kulve <tuomas.kulve@snowcap.fi>
#
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use,
#  copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following
#  conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

import serial
import sys
import re
import os
from time import gmtime, strftime
import sqlite3
import urllib
import json

APIKEY ="Config file format: { 'apikey' : '...' }"
THINGURL = "https://api.thingspeak.com/update"

old_seq = 0
old_timestamp = 0

#
# Turn a json config file into a settings dict
#
def parse_config(conffile):
    global APIKEY

    try:
        config = json.load(open(conffile, 'r'))
        APIKEY = config['apikey']
    except KeyError as e:
        print "Apikey not defined in configuration file '%s'" % conffile
        exit(1)
    except Exception as e:
        print "Error:", e
        print "'%s' is not a valid config file" % conffile
        exit(1)

#
# Parse one line to values
#
def parse_line(line):
    line.rstrip()
    values = line.rsplit()
    values[:0] = [int(strftime("%s", gmtime()))]
    return values

#
# Send statistics to the ThingSpeak
#
# Time         ID      uptime adj    soil    solar  caps    vcc     temp      rssi  lqi
# [1414379517, 'S[0]', '133', '728', '3974', '286', '2050', '2646', '+10.06', '83', '173']
def upload_data(values):
    global old_seq
    global old_timestamp

    timestamp = int(values[0])
    id = values[1]
    seq = int(values[2])
    adj = int(values[3])
    soil = int(values[4])
    solar = int(values[5])
    caps = int(values[6])
    vcc = int(values[7])
    temp = float(values[8])
    rssi = int(values[9])
    lqi = int(values[10])

    params = urllib.urlencode({'api_key': APIKEY, 'timestamp': timestamp, 'field1': seq, 'field2': adj, 'field3': soil, 'field4': solar, 'field5': caps, 'field6': vcc, 'field7': temp, 'field8': rssi})
    print THINGURL, params
    f = urllib.urlopen(THINGURL, params)
    print "http code:", f.getcode()
    print f.read()
    f.close()


#
# Main
#
if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <config file>"
    exit(1)

if len(sys.argv) > 1:
    parse_config(sys.argv[1])

ser = serial.Serial('/dev/ttyACM0', 115200)
while (1):
    line = ser.readline()
    if (line.find('d: ') == -1):
        v = parse_line(line)
        print v
        upload_data(v)



