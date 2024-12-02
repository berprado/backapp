import usb.core
import usb.util

def find_printer():
    # Find all USB devices
    devices = usb.core.find(find_all=True)
    for device in devices:
        print(f"Vendor ID: {device.idVendor:04x}, Product ID: {device.idProduct:04x}")