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
from time import sleep, tzset
from datetime import datetime
import calendar
import sqlite3
import urllib
import json
from collections import deque
import threading

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
    values = [calendar.timegm(datetime.utcnow().timetuple())] + linevalues
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
        print "Value array not the excpected length! Ignoring the data point."
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
    except ValueError as e:
        print "Error getting values:", e
        print "Ignoring the data point."
        return

    if APIKEY == "INVALID":
        print "Status at", datetime.fromtimestamp(timestamp).ctime()
        print "  Seq  :", seq
        print "  Adj  :", adj
        print "  Soil :", soil
        print "  Solar:", solar
        print "  Caps :", caps
        print "  VCC  :", vcc
        print "  Temp :", values[8], "°C"
        print "  RSSI :", rssi
        print "  LQI  :", lqi
    else:
        datestring = datetime.utcfromtimestamp(timestamp).isoformat()
        params = urllib.urlencode({'api_key': APIKEY, 'created_at': datestring, 'field1': seq, 'field2': adj, 'field3': soil, 'field4': solar, 'field5': caps, 'field6': vcc, 'field7': temp, 'field8': lqi})
        print THINGURL, params
        f = urllib.urlopen(THINGURL, params)
        print "http code:", f.getcode()
        print f.read()
        f.close()

class Reader(threading.Thread):
    def __init__(self, queue=None, device=DEVICE, baud_rate=BAUD_RATE):
        threading.Thread.__init__(self)
        self.device = device
        self.baud_rate = baud_rate
        self.q = queue
        self.ser = None

    def run(self):
        while True:
            if self.ser is None:
                try:
                    self.ser = serial.Serial(self.device, self.baud_rate)
                    print "Opened '%s' for reading" % self.device
                except IOError:
                    print "Serial device '%s' not accessible, waiting..." % self.device
                    sleep(2)
                    continue
            try:
                line = self.ser.readline()
            except serial.SerialException:
                self.ser.close()
                self.ser = None
                continue
            if (line.find('d: ') == -1):
                self.q.append(parse_line(line))

#
# Main
#
if len(sys.argv) > 2:
    print "Usage: " + sys.argv[0] + " [config file]"
    exit(1)

if len(sys.argv) > 1:
    parse_config(sys.argv[1])

tzset()
queue = deque()
reader = Reader(queue)
reader.daemon = True
reader.start()
while (1):
    try:
        values = queue.popleft()
        upload_data(values)
    except IndexError:
        # It's ok to have an empty queue
        pass
    except IOError:
        # Send failed, likely due to connection problems. Queue for retry
        queue.appendleft(values)
        print "Error pushing values to ThingSpeak, %d items in queue" % len(queue)

    # Thingspeak enforces a 15s limit on update rate, let's be sure not to
    # violate that. Also to note that if the queue fills up faster than this,
    # we will never empty it...
    sleep(20)



