#!/usr/bin/env python
#
#  Copyright 2015 Tuomas Kulve <tuomas.kulve@snowcap.fi>
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

#
# Check the latest value from a ThingSpeak channel and execute an
# action if moving to alarm zone or moving from alarm zone to safe
# zone.
#

import sys
import os
import json, requests
import argparse
import subprocess

# Parse arguments
parser = argparse.ArgumentParser(description='Test if measurements are within allowed limits.')
parser.add_argument('channel', metavar='channel', type=int, help='ThingSpeak channel id')
parser.add_argument('field', metavar='field', help='ThingSpeak field name')
parser.add_argument('action', metavar='action', help='Executable to run')
parser.add_argument('alarm_limit', metavar='alarm_limit', type=int, help='Alarm limit')
parser.add_argument('safe_limit', metavar='safe_limit', type=int, help='Safe limit')
args = parser.parse_args()

if not os.path.isfile(args.action) or not os.access(args.action, os.X_OK):
    print('"{}" is not an executable'.format(args.action))
    sys.exit(1)

# Check if the alarm limit is a low value or a high value
low_limit = 1
if args.alarm_limit > args.safe_limit:
    low_limit = 0

# Flag file for the alarm
flagfile = '/tmp/tsalarm_{}_{}'.format(str(args.channel), args.field)

# ThingSpeak URL for the latest value
url = 'http://api.thingspeak.com/channels/' + str(args.channel) + '/feeds/last'

resp = requests.get(url=url)
if resp.status_code != 200:
    print('Failed to request ({}): {}'.format(resp.status_code, url))
    sys.exit(1)

data = json.loads(resp.text)
value = int(data[args.field])
is_alarm = (low_limit and value < args.alarm_limit) or (not low_limit and value > args.alarm_limit)
is_safe = (low_limit and value > args.safe_limit) or (not low_limit and value < args.safe_limit)

#print("low_limit: {}, Alarm limit: {}, safe limit: {}, current: {}, alarm: {}, safe: {}".format(low_limit, args.alarm_limit, args.safe_limit, value, is_alarm, is_safe))

# Check for alarm
if is_alarm:
    # Check if alarm has already been signaled
    if os.path.isfile(flagfile):
        sys.exit(0)

    # Create the flag file and signal the alarm
    open(flagfile, 'w').close()
    subprocess.call([args.action, "1", str(value)])
    sys.exit(0)

# Check for safe value
if is_safe:
    # Check if the safe has already been signalled
    if not os.path.isfile(flagfile):
        sys.exit(0)

    # Remove the flag file and signal the alarm
    os.remove(flagfile)
    subprocess.call([args.action, "0", str(value)])
    sys.exit(0)
