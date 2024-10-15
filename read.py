#!/usr/bin/python3

import sys
import time
import logging
import usb

log = logging.getLogger(__name__)
d = usb.core.find(idVendor=0x0fe7, idProduct=0x4001)

if d is None:
    log.error("No Mitutoyo device matching 0fe7:4001 found")
    sys.exit(1)

if d.is_kernel_driver_active(0):
    d.detach_kernel_driver(0)
#except usb.USBError as e:
#    pass # kernel driver is already detached
#    #log.warning(str(e))

d.reset()
d.set_configuration(1)
c = d.get_active_configuration()
epin = d.get_active_configuration().interfaces()[0].endpoints()[0]

bmRequestType0=0x40 # Vendor Host-to-Device
bRequest0=0x01
wValue0=0xA5A5
wIndex0=0


bmRequestType1=0xC0 # Vendor Device-to-Host
bRequest1=0x02
wValue1=0
wIndex1=0
length=1


bmRequestType2=0x40 #0b01000000
bRequest2=0x03
wValue2=0
wIndex2=0
data = b"1\r"


MAX_PKT = 64

while True:
    try:
        d.ctrl_transfer(bmRequestType0, bRequest0, wValue0, wIndex0)
        res1 = d.ctrl_transfer(bmRequestType1, bRequest1, wValue1, wIndex1, length)
        log.debug("Device Vendor resp: {}".format(res1))
        d.ctrl_transfer(bmRequestType2, bRequest2, wValue2, wIndex2, data)
    
        # Attempt to read from the endpoint
        reading = epin.read(MAX_PKT, timeout=500)  # Set a 500ms timeout
        
        # Convert the byte array to a string
        formatted_string = ''.join([chr(byte) for byte in reading]).strip()
        
        # Extract the measurement (assuming the measurement is after 'A+' or 'A-')
        # Example: '01A+00007.09\r'
        if "A+" in formatted_string or "A-" in formatted_string:
            # Find the position where the measurement starts (after 'A+' or 'A-')
            measurement_str = formatted_string.split('A')[1]  # Get everything after 'A'
            sign = measurement_str[0]  # '+' or '-'
            value_str = measurement_str[1:].strip()  # Get the actual number part
            
            # Convert to float and adjust sign if needed
            measurement_value = float(value_str)
            if sign == '-':
                measurement_value = -measurement_value
            
            # Round to 2 decimal places
            measurement_value = round(measurement_value, 2)
            
            # Print the float value
            print(f"Measurement: {measurement_value}")
    
    except usb.core.USBError as e:
        # Handle errors, such as timeouts or device disconnection
        print(f"USBError: {e}")
        break
    time.sleep(0.05)


