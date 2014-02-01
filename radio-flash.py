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
import subprocess
import os
import time
import thread

blob_sent_ok = -1
radio_flash_ok = -1

def read_from_serial(ser, srec_size):
    global blob_sent_ok, radio_flash_ok

    print "*** Reading serial in a separate thread ***"
    while (1):
        line = ser.readline()
        if (line.find('Blob received bytes:') != -1):
            if (line.find('Blob received bytes: '+ str(srec_size)) != -1):
                print "*** Blob sent ***"
                blob_sent_ok = 1
            else:
                print "*** Invalid reply: ***"
                print line
                blob_sent_ok = 0

        if (line.find('radio flash:') != -1):
            if (line.find('radio flash: ok') != -1):
                print "*** Radio flash ok ***"
                radio_flash_ok = 1
            else:
                print "*** Radio flash failed ***"
                radio_flash_ok = 0

        print line.rstrip("\r\n")

def main():
    global blob_sent_ok, radio_flash_ok

    if len(sys.argv) != 2 or (not re.search('\.elf$', sys.argv[1], re.IGNORECASE) and not re.search('\.srec$', sys.argv[1], re.IGNORECASE)):
        print "Usage: " + sys.argv[0] + ": program.elf"
        exit(1)

    filename = sys.argv[1]
    filename_srec = ""

    if re.search('\.elf$', filename, re.IGNORECASE):
        filename_srec = filename.rstrip(".elf") + ".srec"
        print "*** Converting " + filename + " to " + filename_srec + "***"
        subprocess.call(["msp430-objcopy", "-O", "srec", filename, filename_srec + ".tmp"])
        # HACK: Change \r\n to \r as the Control Board's parsing code is flawed
        subprocess.call("tr -d '\n' < " + filename_srec + ".tmp > " + filename_srec, shell=True)
    else:
        filename_srec = filename

    statinfo = os.stat(filename_srec)
    srec_size = statinfo.st_size

    print "*** SREC size: " + str(srec_size) + " ***"

    if (srec_size > 1024*1024):
        print "*** SREC size too large, exiting ***"
        exit(1)

    ser = serial.Serial('/dev/ttyACM0', 115200)

    # Start reading serial in a separate thread
    thread.start_new(read_from_serial, (ser, srec_size,))

    time.sleep(2)

    print "*** Sending SREC ***"
    ser.write("b" + str(srec_size) + "\r")

    srec_content = ""
    with open(filename_srec, 'r') as content_file:
        for line in content_file:
            #print "*** Sending line: ***"
            #print line
            ser.write(line)
            time.sleep(0.01)

    while (blob_sent_ok == -1):
        time.sleep(1)

    if (blob_sent_ok == 0):
        print "*** Failed to sent blob, exiting ***"
        exit(1)

    print "*** Flashing radio ***"

    ser.write("rf\r")

    while (radio_flash_ok == -1):
        time.sleep(1)

    if (radio_flash_ok == 0):
        print "*** Failed to flash radio, exiting ***"
        exit(1)

main()

print "*** DONE ***"

