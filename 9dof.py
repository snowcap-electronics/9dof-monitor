# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200)
#ser.nonblocking()

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])

win = pg.GraphicsWindow()
win.resize(1000,300)
win.setWindowTitle('9dof')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

max_values = 500
p1 = win.addPlot(title="Accelerometer")
curve_x = p1.plot(pen='r')
curve_y = p1.plot(pen='g')
curve_z = p1.plot(pen='b')
data_x = np.arange(max_values)
data_y = np.arange(max_values)
data_z = np.arange(max_values)

p2 = win.addPlot(title="Gyroscope")
gyro_curve_x = p2.plot(pen='r')
gyro_curve_y = p2.plot(pen='b')
gyro_curve_z = p2.plot(pen='g')
gyro_data_x = np.arange(max_values)
gyro_data_y = np.arange(max_values)
gyro_data_z = np.arange(max_values)

p3 = win.addPlot(title="Magnetometer")
magn_curve_x = p3.plot(pen='r')
magn_curve_y = p3.plot(pen='g')
magn_curve_z = p3.plot(pen='b')
magn_data_x = np.arange(max_values)
magn_data_y = np.arange(max_values)
magn_data_z = np.arange(max_values)

def update():
    global curve_x, curve_y, curve_z, data_x, data_y, data_z
    global gyro_curve_x, gyro_curve_y, gyro_curve_z, gyro_data_x
    global gyro_data_y, gyro_data_z, p2
    global mang_curve_x, magn_curve_y, magn_curve_z, magn_data_x
    global magn_data_y, magn_data_z, p3

    has_new_raw = 0
    s_list = []
    start_time = time.time()


    # Read all data from serial
    while (ser.inWaiting()):

        read = ser.readline()
        if (read.find('9dof:') == 1):
            read = read[6:]
            s_list.append(read.split(','))
            has_new_raw += 1

        # Maintain ~60 FPS (~16ms)
        if (time.time() - start_time > 0.016):
            break

    # Make room for new readings
    if has_new_raw:
        data_x = np.roll(data_x, -has_new_raw)
        data_y = np.roll(data_y, -has_new_raw)
        data_z = np.roll(data_z, -has_new_raw)
        gyro_data_x = np.roll(gyro_data_x, -has_new_raw)
        gyro_data_y = np.roll(gyro_data_y, -has_new_raw)
        gyro_data_z = np.roll(gyro_data_z, -has_new_raw)
        magn_data_x = np.roll(magn_data_x, -has_new_raw)
        magn_data_y = np.roll(magn_data_y, -has_new_raw)
        magn_data_z = np.roll(magn_data_z, -has_new_raw)

    # Push readings to the data arrays
    for x in range(has_new_raw):
        i = max_values - (has_new_raw - x)
        data_x[i]      = int(s_list[x][0])
        data_y[i]      = int(s_list[x][1])
        data_z[i]      = int(s_list[x][2])
        gyro_data_x[i] = int(s_list[x][3])
        gyro_data_y[i] = int(s_list[x][4])
        gyro_data_z[i] = int(s_list[x][5])
        magn_data_x[i] = int(s_list[x][6])
        magn_data_y[i] = int(s_list[x][7])
        magn_data_z[i] = int(s_list[x][8])

    # Update plots
    if has_new_raw:
        curve_x.setData(data_x)
        curve_y.setData(data_y)
        curve_z.setData(data_z)
        gyro_curve_x.setData(gyro_data_x)
        gyro_curve_y.setData(gyro_data_y)
        gyro_curve_z.setData(gyro_data_z)
        magn_curve_x.setData(magn_data_x)
        magn_curve_y.setData(magn_data_y)
        magn_curve_z.setData(magn_data_z)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(10)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


