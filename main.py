# main.py (ESP32): LDR drives the LED, publish light once a second,
# status + last will, and commands on bench/<station>/cmd
from time import sleep
from umqtt.simple import MQTTClient

import config
from net import connect_wifi
from lightnode import LightNode

DARK   = 14000
BRIGHT = 51800

STATION = config.STATION
LIGHT  = f"bench/{STATION}/light".encode()
STATUS = f"bench/{STATION}/status".encode()
CMD    = f"bench/{STATION}/cmd".encode()

node = LightNode(adc_pin=34, pwm_pin=25, dark=DARK, bright=BRIGHT)
manual = False          # True while the Pi is controlling the LED


def handle_cmd(topic, msg):
    """Commands from the Pi: led:on, led:off, duty:30000, led:auto"""
    global manual
    text = msg.decode().strip()
    print("cmd:", text)
    try:
        if text == "led:auto":
            manual = False
        elif text == "led:on":
            manual = True
            node.pwm.duty_u16(65535)
        elif text == "led:off":
            manual = True
            node.pwm.duty_u16(0)
        elif text.startswith("duty:"):
            manual = True
            node.pwm.duty_u16(max(0, min(65535, int(text.split(":")[1]))))
        else:
            print("unknown command")
    except ValueError:
        print("bad command value")


def connect_all():
    connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
    client = MQTTClient(f"node-{STATION}", config.BROKER_IP, keepalive=30)
    client.set_callback(handle_cmd)
    client.set_last_will(STATUS, b"offline", retain=True)
    client.connect()
    client.publish(STATUS, b"online", retain=True)
    client.subscribe(CMD, qos=1)
    print("MQTT connected to", config.BROKER_IP)
    return client


client = None
while True:
    pct = node.read_pct()
    if not manual:
        node.set_brightness(pct)          # LED follows the LDR, even if MQTT is down
    try:
        if client is None:
            client = connect_all()
        client.check_msg()
        client.publish(LIGHT, f"{pct:.1f}".encode())
        sleep(1)
    except (OSError, RuntimeError) as e:
        print("Connection problem:", e, "- retrying in 5 s")
        client = None
        sleep(5)