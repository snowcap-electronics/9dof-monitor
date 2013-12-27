# -*- coding: utf-8 -*-
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

#import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial

ser = serial.Serial('/dev/ttyACM0', 9600)

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsWindow(title="Basic plotting examples")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p6 = win.addPlot(title="Updating plot")
curve_x = p6.plot(pen='r')
curve_y = p6.plot(pen='g')
curve_z = p6.plot(pen='b')
data_x = np.arange(1000)
data_y = np.arange(1000)
data_z = np.arange(1000)
print type(data_x)
print data_x.itemsize
ptr = 0

def update():
    global curve_x, curve_y, curve_z, data_x, data_y, data_z, ptr, p6
    read = ser.readline()
    if (read.find('9dof:') == 1):
	read = read[6:]
#	print read
        s_list = read.split(',')
        print s_list[0] + ':' + s_list[1] + ':' + s_list[2]
#        s_list = s_list[1].split(',')
        print int(s_list[0])
        data_x[999] = int(s_list[0])
        data_y[999] = int(s_list[1])
        data_z[999] = int(s_list[2])
        curve_x.setData(data_x)
        curve_y.setData(data_y)
        curve_z.setData(data_z)
        data_x = np.roll(data_x, -1)
        data_y = np.roll(data_y, -1)
        data_z = np.roll(data_z, -1)
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


