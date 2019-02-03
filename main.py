import threading
import Queue
import time
import logging
import paho.mqtt.client as mqtt
import datetime
import bme280
import platform

BRKR='192.168.1.147'
STEM='house/shed'


def sensors(mqtt_q, delay=60):
    logger = logging.getLogger('sensors')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')

    while True:
        logger.info('sensor scan')
        now = datetime.datetime.now().isoformat()
        temperature, pressure, humidity = bme280.readBME280All()

        payload_t = '{0}_{1}_{2}'.format(now, STEM, temperature)
        payload_p = '{0}_{1}_{2}'.format(now, STEM, pressure)
        payload_h = '{0}_{1}_{2}'.format(now, STEM, humidity)

        temp_m = {'topic':'temperature', 'payload':payload_t}
        pressure_m = {'topic':'pressure', 'payload':payload_p}
        humidity_m = {'topic':'humidity', 'payload':payload_h}

        mqtt_q.put(temp_m)
        mqtt_q.put(pressure_m)
        mqtt_q.put(humidity_m)
        time.sleep(delay)
    

def dispatcher(mqtt_q):
    logger = logging.getLogger('dispatcher')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')

    client = mqtt.Client(platform.node())
    client.connect(BRKR)
    client.loop_start()

    while True:
        item = mqtt_q.get()
        logger.info('dispatcher {0} {1}'.format(item['topic'], item['payload']))
        client.publish(item['topic'], item['payload'])


        
def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')

    sound_q = Queue.Queue()
    mqtt_q = Queue.Queue()

    sensors_t = threading.Thread(name='sensors',
                              target = sensors,
                              args = (mqtt_q,))

    dispatcher_t = threading.Thread(name='dispatcher',
                              target = dispatcher,
                              args = (mqtt_q,))

    sensors_t.start()
    dispatcher_t.start()
    main_q.join()
        
if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 autoindent
