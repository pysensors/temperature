import threading
import Queue
import time
import logging
import RPi.GPIO as GPIO
import smbus
import paho.mqtt.client as mqtt
import datetime
import bme280
import platform

BRKR='192.168.1.147'
STEM='house/shed'

def intH(channel):
    print("INTERRUPT")

def gesture(main_q, cancel_q, sound_q):
    port = 1
    bus = smbus.SMBus(port)
    apds = APDS9960(bus)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.IN)

    dirs = {
        ac.APDS9960_DIR_NONE: "none",
        ac.APDS9960_DIR_LEFT: "left",
        ac.APDS9960_DIR_RIGHT: "right",
        ac.APDS9960_DIR_UP: "up",
        ac.APDS9960_DIR_DOWN: "down",
        ac.APDS9960_DIR_NEAR: "near",
        ac.APDS9960_DIR_FAR: "far",
    }


    logger = logging.getLogger('gesture')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')

    GPIO.add_event_detect(7, GPIO.FALLING, callback = intH)
    apds.setProximityIntLowThreshold(50)
    apds.enableGestureSensor()

    while(True):
        time.sleep(0.1)
        if apds.isGestureAvailable():
            motion = apds.readGesture()
            logger.debug('Gesture={0}'.format(dirs.get(motion,'unknown')))
            logger.debug('Gesture={0}'.format(motion))
            sound_q.put(motion)


def screen(main_q, cancel_q, sound_q):
    logger = logging.getLogger('screen')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')

    while(True):
        time.sleep(0.5)
        logger.debug('s loop')

def sound(sound_q):
    logger = logging.getLogger('sound')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('started')
    mixer.init()

    while(True):
        item = sound_q.get()
        logger.debug('sound loop {0}'.format(item))

        if item == ac.APDS9960_DIR_UP: 
            snd = mixer.Sound('click3.wav')
            snd.play()
        if item == ac.APDS9960_DIR_LEFT:
            snd = mixer.Sound('click2.wav')
            snd.play()
        if item == ac.APDS9960_DIR_RIGHT:
            snd = mixer.Sound('click1.wav')
            snd.play()


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

    main_q = Queue.Queue()
    cancel_q = Queue.Queue(maxsize = 1)
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
