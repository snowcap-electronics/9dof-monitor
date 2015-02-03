#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial
import time
import argparse
import sys
import signal

panel_hz = 60.0
gfx_len = 300
derivate_distance_ms = int((1000/panel_hz) / 2)
black = 0
white = 1
state_last_ts = 0
state = []
state.append(black)
state.append(black)

stat_start_ts = 0
stat_data = []
stat_print_counter = 0

mode = "jitter"

switch_mode_start_ts = 0

parser = argparse.ArgumentParser(description='Measure video jitter and latency.')
parser.add_argument('--mode', help='mode {jitter|latency|switch|avsync}')

args = parser.parse_args()

# jitter:  Measure how precisely the frames are flipped
# latency: Measure the time difference between the light sensors
# switch:  Measure the lenght of the black during a mode switch
# avsync:  Measure the time between a beep and a frame change
if args.mode != "jitter" and args.mode != "latency" and args.mode != "switch" and args.mode != "avsync":
    print "Mode must be {jitter|latency|switch|avsync}"
    sys.exit()

mode = args.mode

last_frame_ts = None
fake_ts = 0
ser = serial.Serial('/dev/ttyACM0', 115200)

QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])

if mode == "jitter":
    win = pg.GraphicsWindow()
    win.resize(1000,300)
    win.setWindowTitle('Display measurements')

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    p1 = win.addPlot(title="Frame length")

    curve_f = p1.plot(pen='r')

data_f = np.arange(gfx_len)

data_raw = []
data_raw.append(np.arange(gfx_len))
data_raw.append(np.arange(gfx_len))

total_rawmin = []
total_rawmin.append(4096)
total_rawmin.append(4096)
total_rawmax = []
total_rawmax.append(0)
total_rawmax.append(0)

timestamp = 0
timestamp_old = 0

# Audio related
loudness_max = 0
loudness_min = 99999999
loudness_raw = np.arange(gfx_len)
loudness_state_old = 0
loudness_last_ts = 0

# Clear arrays
for x in range(gfx_len):
    data_raw[0][x]  = 0
    data_raw[1][x]  = 0
    data_f[x]       = 0
    loudness_raw[x] = 0

for x in range(10):
    stat_data.append(0)

def update():
    if mode == "jitter":
        global curve_f, data_f, p1
    global data_raw
    global gfx_len, derivate_distance_ms
    global state_last_ts
    global state, black, white
    global last_frame_ts
    global estimate, double_smoothed, single_smoothed
    global stat_start_ts, stat_print_counter
    global switch_mode_start_ts
    global total_rawmax, total_rawmin
    global timestamp, timestamp_old
    global loudness_max, loudness_min, loudness_raw, loudness_state_old, loudness_last_ts

    has_new_raw = 0
    
    # Read all data from serial
    while (ser.inWaiting()):

        oneline = ser.readline()
        if (oneline.find('adc:') == -1):
            continue

        (ts, loudness, raw1, raw2) = oneline[5:].split(',')
        ts = int(ts)
        # "ts" will overwrap every now and then but otherwise it
        # should be always in 1ms intervals. Let's prepare for losing
        # one sample occasionally though.

        if timestamp_old == 0:
            # First line is special
            timestamp = ts
        elif timestamp_old - ts < 0:
            # Wrap, assume 1ms increment
            timestamp += 1
        else:
            # Should be 1ms increment, but can, in theory, be 2ms occasionally
            timestamp += (timestamp_old - ts)
        timestamp_old = timestamp;

        loudness = int(loudness)
        raw = []
        raw.append(int(raw1))
        raw.append(int(raw2))

        if loudness > loudness_max:
            loudness_max = loudness
        if loudness < loudness_min:
            loudness_min = loudness

        loudness_raw = np.roll(loudness_raw, -1)
        loudness_raw[gfx_len - 1] = int(loudness)

        for i in (0, 1):
            data_raw[i] = np.roll(data_raw[i], -1)
            data_raw[i][gfx_len - 1] = int(raw[i])

            if total_rawmax[i] < raw[i]:
                total_rawmax[i] = raw[i]

            if total_rawmin[i] > raw[i]:
                total_rawmin[i] = raw[i]

        has_new_raw += 1

    if not has_new_raw:
        return


    derivate_threshold = []

    for i in (0, 1):
        # Find the min/max of raw values
        if mode == "jitter":
            rawmax = np.amax(data_raw[i])
            rawmin = np.amin(data_raw[i])
        else:
            rawmax = total_rawmax[i]
            rawmin = total_rawmin[i]

        # "Derivate" threshold is 1/10th of whole scale in short (Hz/2) amount of time
        derivate_threshold.append((rawmax - rawmin)/10.0)

    # Go through all read values starting from the oldest
    for x in range(has_new_raw, 0, -1):
        old_state = []

        for i in (0, 1):
            x_ts = ts - x;
            old_state.append(state[i])

            # Latest "derivate" (not counting in the time spent)
            d = data_raw[i][gfx_len - 1 - x] - data_raw[i][gfx_len - 1 - x - derivate_distance_ms]

            # Check if we are changing frame
            if state[i] == black and d > derivate_threshold[i]:
                state[i] = white
            elif state[i] == white and d < -derivate_threshold[i]:
                state[i] = black

        if mode == "jitter" and (old_state[0] != state[0] or old_state[1] != state[1]):

            # Fake first last timestamp
            if last_frame_ts == None:
                last_frame_ts = x_ts - 16;

            frame_len = x_ts - last_frame_ts
            last_frame_ts = x_ts

            #frame_len = round(frame_len/(1000/panel_hz))

            # Print jitter stats
            if stat_start_ts == 0:
                stat_start_ts = x_ts
            else:
                if x_ts - stat_start_ts > 5*1000:
                    s = ""
                    for x in range(10):
                        s += "{0:6d}".format(stat_data[x])
                        stat_data[x] = 0
                    stat_start_ts = x_ts
                    if stat_print_counter % 10 == 0:
                        print "   0ms  17ms  33ms  50ms  66ms  83ms 100ms 117ms 133ms  high"
                    print s
                    stat_print_counter += 1
                else:
                    frame_slot = int(frame_len)
                    if frame_slot > 9:
                        frame_slot = 9;
                    stat_data[frame_slot] += 1

            data_f = np.roll(data_f, -1)
            data_f[gfx_len - 1] = frame_len
            curve_f.setData(data_f)

            # print "x_ts: {}, s: {}, d: {}, th: {}, len: {}".format(x_ts, state, d, derivate_threshold, frame_len)

        if mode == "switch" and (old_state[0] != state[0]):

            if (state[0] == black):
                # Store the timestamp of white to black transition
                switch_mode_start_ts = x_ts
            else:
                # Print the length of the black period on black to white transition
                print "Mode switch time: {} sec".format((x_ts - switch_mode_start_ts)/1000.0)

        if mode == "avsync":
            loudness_latest = loudness_raw[gfx_len - 1 - x]
            loudness_state = loudness_state_old
            time_diff = 0
            state_change = 0

            # Detect as loudness when over 75% of the max, non-loudness as <50%
            loudness_75 = loudness_min + (loudness_max - loudness_min) * 0.75
            loudness_50 = loudness_min + (loudness_max - loudness_min) * 0.50
            if loudness_latest > loudness_75:
                loudness_state = 1
            if loudness_latest < loudness_50:
                loudness_state = 0

            # New beep start detected (audio late)
            if loudness_state_old != loudness_state and loudness_state == 1:
                time_diff = loudness_last_ts - state_last_ts
                loudness_last_ts = timestamp
                state_change = 1

            loudness_state_old = loudness_state

            # New white frame detected (audio early)
            if old_state[0] != state[0] and state[0] == white:
                time_diff = state_last_ts - loudness_last_ts
                # audio early i.e. negative diff
                time_diff *= -1
                state_last_ts = timestamp
                state_change = 1

            # Assume >500ms A/V sync diff is just comparing wrong states
            if state_change and time_diff > -500 and time_diff < 500:
                print "A/V sync diff: {} ms".format(time_diff)

def quit(signum, frame):
    sys.exit(1)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


