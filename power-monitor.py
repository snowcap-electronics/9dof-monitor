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

# SQL Queries
#
# For csv output:
# .header on
# .mode csv
#
# Sum of Wh per hour:
# SELECT strftime('%Y-%m-%d-%H', date, 'unixepoch'), sum(blinks) FROM current GROUP BY strftime('%Y-%m-%d-%H', date, 'unixepoch');

DBPATH = '/home/kulve/projects/flyingfox/current.db'

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
# Main
#
if len(sys.argv) != 1:
    print "Usage: " + sys.argv[0]
    exit(1)

db = init_db()

ser = serial.Serial('/dev/ttyACM0', 115200)
while (1):
    line = ser.readline()
    if (line.find('P: ') != -1):
        if (line.find('d: ') != -1):
            print "Invalid line (d:):"
            print line
            continue
        v = parse_line(line)
        if (len(v) != 7):
            print "Invalid line (len != 7):"
            print line
            continue
        insert_db(db, v)

