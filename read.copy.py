#!/usr/bin/python3

import time
import usb.core
import sys
import threading
import logging

# Function to read from a USB device
def read_device(device):
    print(f"Handling Mitutoyo device on Bus: {device.bus}, Device: {device.address}")
    
    # Detach kernel driver if necessary
    if device.is_kernel_driver_active(0):
        device.detach_kernel_driver(0)

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
    
    while True:  # Keep reading from this device indefinitely
        try:
            log = logging.getLogger(__name__)
            
            d.ctrl_transfer(bmRequestType0, bRequest0, wValue0, wIndex0)
            res1 = d.ctrl_transfer(bmRequestType1, bRequest1, wValue1, wIndex1, length)
            log.debug("Device Vendor resp: {}".format(res1))
            d.ctrl_transfer(bmRequestType2, bRequest2, wValue2, wIndex2, data)
            
            # Attempt to read from the endpoint
            reading = epin.read(64, timeout=500)  # Set a 500ms timeout
            
            # Convert the byte array to a string
            formatted_string = ''.join([chr(byte) for byte in reading]).strip()
            
            # Extract the measurement (assuming the measurement is after 'A+' or 'A-')
            if "A+" in formatted_string or "A-" in formatted_string:
                measurement_str = formatted_string.split('A')[1]
                sign = measurement_str[0]
                value_str = measurement_str[1:].strip()
                
                # Convert to float and adjust sign if needed
                measurement_value = float(value_str)
                if sign == '-':
                    measurement_value = -measurement_value
                
                # Round to 2 decimal places
                measurement_value = round(measurement_value, 2)
                
                # Print the float value with bus and device address
                print(f"Bus {device.bus}, Device {device.address}, Measurement: {measurement_value}")

        except usb.core.USBError as e:
            # Handle timeout or other USB errors
            if e.errno == 110:
                print(f"Bus {device.bus}, Device {device.address}, Timeout occurred, trying again...")
            else:
                print(f"Bus {device.bus}, Device {device.address}, USBError: {e}")
                break

# Find all devices matching the given vendor and product ID
devices = usb.core.find(idVendor=0x0fe7, idProduct=0x4001, find_all=True)

if devices is None:
    print("No Mitutoyo devices found")
    sys.exit(1)

threads = []

try:
    # Create a thread for each device
    for i, d in enumerate(devices, start=1):
        thread = threading.Thread(target=read_device, args=(d,))
        threads.append(thread)
        thread.start()  # Start the thread

    # Wait for all threads to complete (which will be never in this case)
    for thread in threads:
        thread.join()  # This will block until the thread terminates, which won't happen until interrupted

except KeyboardInterrupt:
    print("\nTerminating the program. Goodbye!")
    sys.exit(0)

