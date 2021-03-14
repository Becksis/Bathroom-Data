import micropython
from umqtt.simple import MQTTClient
import network
import machine
import time
import utime
import dht
import gc
from machine import Pin, I2C, Timer
from imu import MPU6050
import ntptime
import main_website


ssid = 'WiFi-2.4-E786'
pwd = 'pws3XNq269QQ'
device_name = 'minimo_dlsp'  
#mqtt_server = '192.168.2.129' 
mqtt_server = 'test.mosquitto.org'
mqtt_port = 1883  
mqttConnected = False

#Funktion, um Zeit zu setzen
def zeit():
    now=time.time()
    ntptime.settime()
    a = time.localtime(now+3600)
    return(a)

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to ' + ssid)
        wlan.connect(ssid, pwd)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
#Für IMU Sensor    
i2c = machine.I2C(scl=Pin(0), sda=Pin(4), freq=100000)
mpu6050 = MPU6050(i2c)

def start_sampling(d):
    client = MQTTClient(device_name, mqtt_server, mqtt_port)
    mqttConnected=client.connect()
      
    #IMU SENSOR
    accel = mpu6050.accel
    gyro = mpu6050.gyro
    accel1 = accel.xyz
    gyro1 = gyro.xyz
    accel2 = list(accel1)
    gyro2 = list(gyro1)
        
    #DHT22 SENSOR
    d.measure()
    tempValue = d.temperature()
    humidity = d.humidity() 
    
    #MOIST SENSOR
    adc = machine.ADC(0)
    moisture = -0.2451 * float(adc.read()) + 211.6
    #moistString = "{:2.0f}".format(moisture) + "%\n"
    
    #Setzen der Zeit
    a = zeit()
        
    print(a)
    
    s = '{ "device":"' + str(device_name) +\
     '","temp": ' + str(tempValue) + \
     ',"humi": ' + str(humidity) + \
     ',"moist": ' + str(moisture) + \
     ',"accel": ' + str(accel2) + \
     ',"gyro": ' + str(gyro2) + \
     ', "time":"' + str(a) + '"}'
      
    print(s)
    client.publish('/iot_wernick/data', s) #topic für mqtt
    client.disconnect()
    
def set_led(v):
    if v == 1:
        led.on()
    else:
        led.off()

led = machine.Pin(2, machine.Pin.OUT)
d = dht.DHT22(machine.Pin(14))  
do_connect()

while True:
    try:    
        set_led(0)
        start_sampling(d)
        set_led(1)
        utime.sleep(1) #alle 2 Sekunden messen
    except Exception as e:
        print(e)




