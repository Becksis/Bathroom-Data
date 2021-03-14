import micropython
from umqtt.simple import MQTTClient
from imu import MPU6050
import network
import machine
import time
import utime
import ntptime
import dht
import gc
from machine import Pin, I2C, Timer

ssid = 'HabtIhrWlan'
pwd = 'Motivationslolli69'
device_name = 'terminator' 
mqtt_server = 'test.mosquitto.org'
mqtt_port = 1883
mqttConnected = False

wlan = None
#topic = "/iot_beck/data"

#Wlan-Connection herstellen:
def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to ' + ssid)
        wlan.connect(ssid, pwd)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

#Zeit anpassen, +3600 für Winterzeit
def zeit():
    now=time.time()
    ntptime.settime()
    a = time.localtime(now+3600)
    return(a)

#Einlesen der Werte des IMU Sensors
def window():  
    i2c = machine.I2C(scl=Pin(5), sda=Pin(4), freq=100000)
    mpu6050 = MPU6050(i2c)
    gyro = mpu6050.gyro
    gyro1 = gyro.xyz
    gyro_list = list(gyro1)
    #ersten beiden Werte, Beschleunigung x,y
    #z wird nicht beschleunigt im vorligenden Fall
    gyro_x = round(gyro_list[0], 1)
    gyro_y = round(gyro_list[1],1)
    gyro_values = [gyro_x, gyro_y]
    return(gyro_values)

#DHT22 Daten einlesen
def ht():
    d = dht.DHT22(machine.Pin(0))
    d.measure()
    tempValue = d.temperature()
    humidity = d.humidity()
    return(tempValue, humidity)

#Zusammenfassen der Sensordaten in eine liste
def values():
    #gyro
    gyro_value_list = window()
    g_x = gyro_value_list[0]
    g_y = gyro_value_list[1]
    #dht
    temp_hum = ht()
    temp_hum1 = list(temp_hum)
    t = temp_hum1[0]
    h = temp_hum1[1]
    value_list = [g_x, g_y, t, h]
    return(value_list)

#LED, um zu sehen, wenn gemessen wird
def set_led(v):
    if v == 1:
        led.on()
    else:
        led.off()
        
#Funktion, um Werte zu senden
def sampling(n):
    if wlan is not None and not wlan.isconnected():
        do_connect()

    client = MQTTClient(device_name, mqtt_server, mqtt_port)
    mqttConnected=client.connect()
    #Listen werden für Verdichtung genutzt
    gx_list = []
    gy_list =[]
    temp_list=[]
    hum_list=[]
    #Es werden immer 20 Werte betrachtet
     while len(n) < 20:
        try:
            set_led(0)
            #Liste mit Werten aus Funktion
            s = values()  
            print(s)
            n.append(1)
            print(len(n))
            #Aufteilen der Wertliste
            #jeweiligen Werte neuer Liste angehangen
            s1 = s[0]
            gx_list.append(s1)
            s2 = s[1]
            gy_list.append(s2)
            s3 = s[2]
            temp_list.append(s3)
            s4 = s[3]
            hum_list.append(s4)
            
            set_led(1)
            #ca. messen ca. jede halbe Sekunde
            utime.sleep(0.5) 
        except Exception as e:
            print(e)
    else:      
        #Gyro-x auf Überschreitung der Toleranz überprüfen
        if min(gx_list) < -5: 
            gx_value = 1 #Fenster wird geöffnet
        elif max(gx_list) > 0:
            gx_value = -1 #Fenster wird geschlossen
        else:
            gx_value = 0 #wenn nichts passiert, dann 0
            
        #Gyro-y auf Überschreitung der Toleranz überprüfen
        if max(gy_list) < -8:  
            gy_value = 1 #Fenster wird geöffnet
        elif min(gy_list) > 8: 
            gy_value = -1 # Fenster wird geschlossen
        else:
            gy_value = 0 #wenn nichts passiert, dann 0
            
        #Durchschnittswerte der Listen für temp und humi        
        temp_avg = round(sum(temp_list) / len(temp_list), 1)
        hum_avg = round(sum(hum_list) / len(hum_list), 1)
        a = zeit()
        
        send_list = [gx_value, gy_value, temp_avg, hum_avg, a]
        print(send_list)
        #Für die letzten 20 Werte wird nur ein Json-Objekt übergeben
        #abhängig von Übersteigen des Toleranzbandes 
        send = '{ "device":"' + str(device_name) +\
         '","temp": ' + str(temp_avg) + \
         ',"humi": ' + str(hum_avg) + \
         ',"gyro_x": ' + str(gx_value) + \
         ',"gyro_y": ' + str(gy_value) + \
         ', "time":"' + str(a) + '"}'

        client.publish('/iot_beck/data', send)
        client.disconnect()     
        #print('Liste wird nun geleert')
        #nach 20 Durchläufen, wird Liste geleert
        n.clear()       

led = machine.Pin(2, machine.Pin.OUT)
d = dht.DHT22(machine.Pin(0))
do_connect()

while True:
    try:
        n = []
        sampling(n)
    except Exception as e:
        print (e)




