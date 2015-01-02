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

# SQL Queries
#
# For csv output:
# .header on
# .mode csv
#
# Sum of Wh per hour:
# SELECT strftime('%Y-%m-%d-%H', date, 'unixepoch'), sum(blinks), avg(battery) FROM current GROUP BY strftime('%Y-%m-%d-%H', date, 'unixepoch');

#DBPATH = os.environ['HOME'] + '/projects/flyingfox/current.db'
DBPATH = '/home/pi/projects/flyingfox/current.db'
APIKEY =""
THINGURL = "https://api.thingspeak.com/update"


old_seq = 0
old_timestamp = 0

#
# Init DB
#
def init_db():
    conn = sqlite3.connect(DBPATH)
    c = conn.cursor()
    # Create table if not yet found
    c.execute('''CREATE TABLE IF NOT EXISTS current
             (date TIMESTAMP,
              counter INTEGER,
              battery INTEGER,
              temperature FLOAT,
              blinks INTEGER,
              rssi INTEGER,
              lqi INTEGER)''')
    return conn

#
# Insert a line to DB
#
def insert_db(conn, values):
    c = conn.cursor()
    vstr = ','.join(values)
    dbcmd = "INSERT INTO current VALUES (%s)" % vstr
    print dbcmd
    c.execute(dbcmd)
    conn.commit()

#
# Parse one line to values
#
def parse_line(line):
    line.rstrip()
    values = line.rsplit()
    # Replace "P:" with current time
    values[0] = strftime("%s", gmtime())
    return values

#
# Send statistics to the Phant
#
# 1406881422,43079,3129,+22.81,66,126,175
def upload_data(values):
    global old_seq
    global old_timestamp

    timestamp = int(values[0])
    seq = int(values[1])
    batt = int(values[2])
    temp = float(values[3])
    # WAR, currently counts both rising and falling edges
    blinks = int(int(values[4]) / 2)
    rssi = int(values[5])
    lqi = int(values[6])

    if old_seq == 0:
        old_seq = seq
        old_timestamp = timestamp
        return

    # Assume steady consumption and count the average if missing transmissions
    skips = seq - old_seq
    blinks = skips * blinks

    time_sec = timestamp - old_timestamp
    power = int(blinks * (3600 / float(time_sec)) + 0.5)
    #params = urllib.urlencode({'timestamp': timestamp, 'batt': batt, 'temp': temp, 'power': power, 'rssi': rssi, 'lqi': lqi})
    #url = PHANTURL + "&" + params
    params = urllib.urlencode({'api_key': APIKEY, 'timestamp': timestamp, 'field1': seq, 'field2': batt, 'field3': temp, 'field4': power, 'field5': rssi, 'field6': lqi})
    print THINGURL, params
    f = urllib.urlopen(THINGURL, params)
    print "http code:", f.getcode()
    print f.read()
    f.close()


#
# Main
#
if len(sys.argv) != 1:
    print "Usage: " + sys.argv[0]
    exit(1)

db = init_db()

ser = serial.Serial('/dev/ttyACM0', 115200)
while (1):
    line = ser.readline()
    if (line.find('d: ') != -1):
        continue

    if (line.find('P: ') != -1):
        v = parse_line(line)
        if (len(v) != 7):
            print "Invalid line (len != 7):"
            print line
            continue
        insert_db(db, v)
        upload_data(v)

    if (line.find('S[0]: ') != -1):
        v = parse_line(line)
        if (len(v) != 11):
            print "Invalid line (len != 11):"
            print line
            continue
        print line

