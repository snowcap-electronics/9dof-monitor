# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial
import time

panel_hz = 60.0
gfx_len = 300
derivate_distance_ms = int((1000/panel_hz) / 2)
black = 0
white = 1
state = []
state.append(black)
state.append(black)

stat_start_ts = 0
stat_data = []
stat_print_counter = 0

last_frame_ts = None
fake_ts = 0
ser = serial.Serial('/dev/ttyACM0', 115200)

QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])

win = pg.GraphicsWindow()
win.resize(1000,300)
win.setWindowTitle('Display measurements')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Frame length (ms)")
curve_f = p1.plot(pen='r')
data_f = np.arange(gfx_len)
data_raw = []
data_raw.append(np.arange(gfx_len))
data_raw.append(np.arange(gfx_len))

# jitter: Measure how precisely the frames are flipped
# latency: Measure the time difference between the light sensors
# switch: Measure the lenght of the black during a mode switch
mode = "switch"

switch_mode_start_ts = 0

total_rawmin = []
total_rawmin.append(4096)
total_rawmin.append(4096)
total_rawmax = []
total_rawmax.append(0)
total_rawmax.append(0)

# Clear arrays
for x in range(gfx_len):
    data_raw[0][x] = 0
    data_raw[1][x] = 0
    data_f[x] = 0

for x in range(10):
    stat_data.append(0)

def update():
    global curve_f, data_f, p1, data_raw
    global gfx_len, derivate_distance_ms
    global state, black, white
    global last_frame_ts
    global estimate, double_smoothed, single_smoothed
    global stat_start_ts, stat_print_counter
    global switch_mode_start_ts
    global total_rawmax, total_rawmin

    has_new_raw = 0
    
    # Read all data from serial
    while (ser.inWaiting()):

        oneline = ser.readline()
        if (oneline.find('adc:') == -1):
            continue

        (ts, raw1, raw2) = oneline[5:].split(',')
        ts = int(ts)
        raw = []
        raw.append(int(raw1))
        raw.append(int(raw2))

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

            frame_len = round(frame_len/(1000/panel_hz))

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

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


