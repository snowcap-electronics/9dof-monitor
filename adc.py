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
state = black
last_frame_ts = None
fake_ts = 0
ser = serial.Serial('/dev/ttyACM0', 115200)

# BrownLinearExpo
estimate = 0.0
double_smoothed = 1.0
single_smoothed = 1.0

QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])

win = pg.GraphicsWindow()
win.resize(1000,300)
win.setWindowTitle('9dof')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Frame length (ms)")
curve_f = p1.plot(pen='r')
data_f = np.arange(gfx_len)
data_raw = np.arange(gfx_len)

# Clear arrays
for x in range(gfx_len):
    data_raw[x] = 0
    data_f[x] = 0

def update():
    global curve_f, data_f, p1, data_raw
    global gfx_len, derivate_distance_ms
    global state, black, white
    global last_frame_ts
    global estimate, double_smoothed, single_smoothed
    
    has_new_raw = 0
    
    # Read all data from serial
    while (ser.inWaiting()):

        oneline = ser.readline()
        if (oneline.find('adc:') != -1):
            a = 0.1

            (ts, raw) = oneline[5:].split(',')
            ts = int(ts)
            raw = int(raw)

            # BrownLinearExpo
            measurement = float(raw)
            single_smoothed = a * measurement + (1 - a) * single_smoothed;
            double_smoothed = a * single_smoothed + (1 - a) * double_smoothed;
            est_a = (2*single_smoothed - double_smoothed);
            est_b = (a / (1-a) )*(single_smoothed - double_smoothed);
            estimate = est_a + est_b;

            #print str(ts) + "," + str(raw) + "," + str(estimate)
            data_raw = np.roll(data_raw, -1)
            data_raw[gfx_len - 1] = int(raw)
            has_new_raw += 1

    if not has_new_raw:
        return

    # Find the min/max of raw values
    rawmax = np.amax(data_raw)
    rawmin = np.amin(data_raw)

    # "Derivate" threshold is 1/10th of whole scale in short amount of time
    derivate_threshold = ((rawmax - rawmin)/10)

    # Go through all read values starting from the oldest
    for x in range(has_new_raw, 0, -1):
        x_ts = ts - x;
        old_state = state

        # Latest "derivate" (not counting in the time spent)
        d = data_raw[gfx_len - 1 - x] - data_raw[gfx_len - 1 - x - derivate_distance_ms]

        #print "{},{},{}".format(x_ts, state*2000, data_raw[gfx_len - 1 - x])
        #print "ts: {}, state: {}, d: {}, th: {}, d_ms: {}, (min/max: {}/{})".format(x_ts, state, d, derivate_threshold, derivate_distance_ms, rawmin, rawmax)

        # Check if we are changing frame
        if state == black and d > derivate_threshold:
            state = white
        elif state == white and d < -derivate_threshold:
            state = black

        if old_state != state:

            # Fake first last timestamp
            if last_frame_ts == None:
                last_frame_ts = x_ts - 16;

            frame_len = x_ts - last_frame_ts
            last_frame_ts = x_ts

            frame_len = round(frame_len/(1000/panel_hz))

            # Hackish
            #if frame_len > 100 or frame_len < 4:
            #    continue

            data_f = np.roll(data_f, -1)
            data_f[gfx_len - 1] = frame_len
            curve_f.setData(data_f)

            print "x_ts: {}, s: {}, d: {}, th: {}, len: {}, (min/max: {}/{})".format(x_ts, state, d, derivate_threshold, frame_len, rawmin, rawmax)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


