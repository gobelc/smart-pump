import machine
import webrepl
import network

## Change the WLAN config
SSID = ""
password = ""

def do_connect():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(SSID, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


do_connect()
webrepl.start()

