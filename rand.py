# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial

ser = serial.Serial('/dev/ttyACM0', 9600)

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])

win = pg.GraphicsWindow()
win.resize(1000,300)
win.setWindowTitle('9dof')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Accelerometer")
curve_x = p1.plot(pen='r')
curve_y = p1.plot(pen='g')
curve_z = p1.plot(pen='b')
data_x = np.arange(1000)
data_y = np.arange(1000)
data_z = np.arange(1000)
ptr = 0

p2 = win.addPlot(title="Gyroscope")
gyro_curve_x = p2.plot(pen='r')
gyro_curve_y = p2.plot(pen='b')
gyro_curve_z = p2.plot(pen='g')
gyro_data_x = np.arange(1000)
gyro_data_y = np.arange(1000)
gyro_data_z = np.arange(1000)

p3 = win.addPlot(title="Magnetometer")
magn_curve_x = p3.plot(pen='r')
magn_curve_y = p3.plot(pen='g')
magn_curve_z = p3.plot(pen='b')
magn_data_x = np.arange(1000)
magn_data_y = np.arange(1000)
magn_data_z = np.arange(1000)

def update():
    global curve_x, curve_y, curve_z, data_x, data_y, data_z, ptr, p6
    global gyro_curve_x, gyro_curve_y, gyro_curve_z, gyro_data_x
    global gyro_data_y, gyro_data_z, p2
    global mang_curve_x, magn_curve_y, magn_curve_z, magn_data_x
    global magn_data_y, magn_data_z, p3
    read = ser.readline()
    if (read.find('9dof:') == 1):
	read = read[6:]
        s_list = read.split(',')
        data_x[999] = int(s_list[0])
        data_y[999] = int(s_list[1])
        data_z[999] = int(s_list[2])
	gyro_data_x[999] = int(s_list[3])
	gyro_data_y[999] = int(s_list[4])
	gyro_data_z[999] = int(s_list[5])
	magn_data_x[999] = int(s_list[6])
	magn_data_y[999] = int(s_list[7])
	magn_data_z[999] = int(s_list[8])
        curve_x.setData(data_x)
        curve_y.setData(data_y)
        curve_z.setData(data_z)
	gyro_curve_x.setData(gyro_data_x)
	gyro_curve_y.setData(gyro_data_y)
	gyro_curve_z.setData(gyro_data_z)
	magn_curve_x.setData(magn_data_x)
	magn_curve_y.setData(magn_data_y)
	magn_curve_z.setData(magn_data_z)
        data_x = np.roll(data_x, -1)
        data_y = np.roll(data_y, -1)
        data_z = np.roll(data_z, -1)
        gyro_data_x = np.roll(gyro_data_x, -1)
        gyro_data_y = np.roll(gyro_data_y, -1)
        gyro_data_z = np.roll(gyro_data_z, -1)
        magn_data_x = np.roll(magn_data_x, -1)
        magn_data_y = np.roll(magn_data_y, -1)
        magn_data_z = np.roll(magn_data_z, -1)
#    if ptr == 0:
#        p6.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
        ptr += 1
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


