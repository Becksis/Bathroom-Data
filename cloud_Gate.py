import datetime
import paho.mqtt.client as mqtt
import json
import calendar
from pymongo import MongoClient

#Connection mit online Mongo DB Atlas database, username:moritz, password: dlsp
client = MongoClient("mongodb+srv://moritz:dlsp@cluster0.sramn.mongodb.net/moritz?retryWrites=true&w=majority")
#DB name: iot_dlsp
db = client.get_database('iot_beck')
#mqtt_server="127.0.0.1"
mqtt_server="test.mosquitto.org"
#mqtt_port=1884
mqtt_port=1883
topic = "/iot_beck/data"

def on_connect(mqttc, obj, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(topic)

def on_message(client, userdata, msg):
    v=str(msg.payload.decode('utf8')) #string comes in as bytes so need to convert it
    sample=json.loads(v)
    print("Data Received")
    t=str(sample['time'])
    print(t)
    t=t[1:]
    t=t[:-1]
    t=t.split(",")
    #print(t)
    time_t=datetime.datetime(int(t[0]), int(t[1]), int(t[2]),int(t[3]), int(t[4]),int(t[5]), int(t[6])) #, int(t[7])
    print(time_t)
    timestamp_utc = calendar.timegm(time_t.timetuple())
    #print(timestamp_utc)
    #print('Processing sample : ' + str(sample['value']))
    body= {'device' : str(sample['device']),'sample_date' : time_t.strftime("%Y-%m-%d"),'temp' : float(sample['temp']),
           'humi' : float(sample['humi']), 'gyro_x' : float(sample['gyro_x']),'gyro_y' : float(sample['gyro_x']),'time' : repr(timestamp_utc) }
    print(body)

    #in Datenbank schreiben, Collection called 'sensor2'
    result = db.bathroom_update3.insert_one(body)

    # Step 4: Print to the console the ObjectID of the new document
    print('Datensatz {0} geschrieben.'.format(result.inserted_id))

def on_log(mqttc, obj, level, string):
    print(string)
    print('Connecting to MQTT broker')
try:
    client = mqtt.Client()
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_log = on_log
    client.connect(mqtt_server, mqtt_port, 60)
    client.loop_forever()
except Exception as e:
    print("oh nooo", e)
