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
from time import gmtime, mktime, ctime, tzset, timezone
import sqlite3
import urllib
import json

APIKEY ="INVALID"
THINGURL = "https://api.thingspeak.com/update"

DEVICE = "/dev/ttyACM0"
BAUD_RATE = 115200

old_seq = 0
old_timestamp = 0

#
# Turn a json config file into a settings dict
# Config file format: { 'apikey' : '...',  'device' : '/dev/...', ...  }
#
def parse_config(conffile):
    global APIKEY
    global DEVICE
    global BAUD_RATE

    try:
        config = json.load(open(conffile, 'r'))
    except Exception as e:
        print "Error:", e
        print "'%s' is not a valid config file" % conffile
        exit(1)

    try:
        APIKEY = config['apikey']
    except KeyError as e:
        pass

    try:
        DEVICE = config['device']
    except KeyError as e:
        pass

    try:
        BAUD_RATE = config['baud_rate']
    except KeyError as e:
        pass

#
# Parse one line to values
#
def parse_line(line):
    line.rstrip()
    linevalues = line.rsplit()
    values = [mktime(gmtime())] + linevalues
    return values

#
# Send statistics to the ThingSpeak or print locally if no apikey
#
# Time         ID      uptime adj    soil    solar  caps    vcc     temp      rssi  lqi
# [1414379517, 'S[0]', '133', '728', '3974', '286', '2050', '2646', '+10.06', '83', '173']
def upload_data(values):
    global APIKEY
    global old_seq
    global old_timestamp

    if len(values) < 11:
        return

    try:
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
    except ValueError:
        return

    if APIKEY == "INVALID":
        print "Status at", ctime(timestamp - timezone)
        print "  Seq:", seq
        print "  Adj:", adj
        print "  Soil:", soil
        print "  Solar:", solar
        print "  Caps:", caps
        print "  VCC:", vcc
        print "  Temp:", values[8], "°C"
        print "  RSSI:", rssi
    else:
        params = urllib.urlencode({'api_key': APIKEY, 'timestamp': timestamp, 'field1': seq, 'field2': adj, 'field3': soil, 'field4': solar, 'field5': caps, 'field6': vcc, 'field7': temp, 'field8': rssi})
        print THINGURL, params
        f = urllib.urlopen(THINGURL, params)
        print "http code:", f.getcode()
        print f.read()
        f.close()

#
# Main
#
if len(sys.argv) > 2:
    print "Usage: " + sys.argv[0] + " [config file]"
    exit(1)

if len(sys.argv) > 1:
    parse_config(sys.argv[1])

ser = serial.Serial(DEVICE, BAUD_RATE)

tzset()
while (1):
    line = ser.readline()
    if (line.find('d: ') == -1):
        v = parse_line(line)
        upload_data(v)



