import network, time, config

w = network.WLAN(network.STA_IF)
w.active(True)


if not w.isconnected():
    w.disconnect()
    time.sleep(1)
    w.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    

for _ in range(40):
    if w.isconnected():
        break
    time.sleep(1.5)

print(w.isconnected(), w.status(), w.ifconfig())