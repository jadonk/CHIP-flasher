#!/usr/bin/env python
from serialconnection import SerialConnection
from unittest import TestCase, TextTestRunner, TestLoader
from observable_test import *
from commandRunner import CommandRunner
from deviceDescriptor import DeviceDescriptor
import os
import re
import time
import io
import serial
from ui_strings import *

LOGIN = 'root'
PASSWORD = 'chip'
ALL_TESTS_PASSED_REGEX = re.compile(r'.*### ALL TESTS PASSED ###.*')

dummy = DeviceDescriptor.makeDummy()

CONNECT_TIME = 60
FINE_SERIAL_TIME = 45



# This is Alex's code. 
#------------------------------------------------------------------
def answer_prompt(sio,prompt_to_wait_for,answer_to_write,send_cr=True):
#------------------------------------------------------------------
  sio.flush()
  prompt_found = False
  data = ''
  #if send_cr:
    #sio.write(unicode('\n'))

  d='something'
  while not len(d)==0:
    d = sio.read(2000);
    data += d
    print '-' * 50
    print ' %d bytes read' % (len(data))
    print '-' * 50

  print data

  while not prompt_found:
    d = sio.read(100);
    data += d
    print '-' * 50
    print ' %d bytes read' % (len(data))
    print '-' * 50
    if(data[:-1].endswith(prompt_to_wait_for)):
        sio.write(unicode(answer_to_write+'\n'))
        print '-' * 50
        print ' detected [%s] ' % prompt_to_wait_for
        print '-' * 50
        prompt_found = True
    else:
        if send_cr:
          sio.write(unicode('\n'))
    sio.flush()
    #sys.stdin.readline()

#------------------------------------------------------------------
def scanfor(sio,regexp_to_scan_for,answer_to_write):
#------------------------------------------------------------------
  prompt_found = False
  data = ''
  while not prompt_found:
    data += sio.read(100);
    print '-' * 50
    print ' %d bytes read' % (len(data))
    print '-' * 50
    print data
    if re.search(regexp_to_scan_for,data):
        print '-' * 50
        print ' detected [%s] ' % regexp_to_scan_for
        print '-' * 50
        sio.write(unicode(answer_to_write+'\n'))
        prompt_found = True
    sio.flush()
  return data


#------------------------------------------------------------------
def test(serial_port):
#------------------------------------------------------------------

  print 'reading from %s:' % serial_port

  ser = serial.Serial(serial_port,115200, timeout=1, xonxoff=True);
  sio = io.TextIOWrapper(io.BufferedRWPair(ser,ser))

  #login

  answer_prompt(sio,'login:','root')
  answer_prompt(sio,'Password:','chip',False)
  answer_prompt(sio,'#','hwtest')
  d=scanfor(sio,r'.*### [^#]+ ###.*','poweroff')

  if re.search(r'.*### ALL TESTS PASSED ###.*',d):
    print "---> TESTS PASSED"
    ser.close();
    return 0, d
    
  ser.close();
  
  print "---> TESTS FAILED"
  return 1 , d


#end of Alex's code
class ChipHardwareTest(TestCase):
    '''
    This will wait for CHIP to boot up, log in, and then run 'hwtest' on it
    '''

    def setUp(self):
        self.progressObservers = []
        try:
            self.deviceDescriptor = self.attributes['deviceDescriptor']
        except: # run from regular unit test
            global dummy
            self.deviceDescriptor = dummy # a dummy object
            self.deviceDescriptor.serial = "/dev/chip-2-1-serial"
    
    def findSerialDevice(self):
#         print "find serial device"
#         print self.deviceDescriptor.serial
        return os.path.exists(self.deviceDescriptor.serial)

 
        
    @label(UI_WAITING_FOR_DEVICE)
    @progress(FINE_SERIAL_TIME)
    @failMessage(FAIL_301_TEXT)
    def test_000_serial(self):
        for attempt in range(1,FINE_SERIAL_TIME):
            if self.findSerialDevice():
                return
            time.sleep(1)
        raise Exception("No Serial device found: " + self.deviceDescriptor.serial)
    
    @label(UI_HARDWARE_TEST)
    @progress(45)
    @failMessage(FAIL_302_TEXT)
    def test_020_hwtest(self):
        result, details = test(self.deviceDescriptor.serial)
        if not hasattr(self,"output"):
            self.output = ""
        self.output += details
    
        self.assertEqual(0,result)

def main():
    tl = TestLoader()
    suite = tl.loadTestsFromTestCase(ChipHardwareTest)
    result = TextTestRunner(verbosity=2, failfast=True).run(suite) # This runs the whole suite of tests. For now, using TextTestRunner
    print result

#------------------------------------------------------------------
if __name__ == "__main__":
#------------------------------------------------------------------
  exit( main() )
