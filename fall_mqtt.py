#m.py
import paho.mqtt.client as mqtt
import numpy as np
import requests
import json
import math

client = mqtt.Client(protocol=mqtt.MQTTv311)
api_key = "AIzaSyCIBBs236c9A0tyO6nTpbD6wWFamWIDyYA"

def on_connect(client, userdata, flags, rc):    
    print("Result from connect: {}".format(mqtt.connack_string(rc)))    
    # Subscribe to the arduino/falls topic filter 
    client.subscribe("arduino/falls")                                 

def on_subscribe(client, userdata, mid, granted_qos):    
    print("I've subscribed")

def on_message(client, userdata, msg):    
    print("Message received. Topic: {}. Payload: {}".format(
        msg.topic, str(msg.payload)))
    
    payload = eval(msg.payload)
    
    c1 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Az"],2))
    c2 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Ay"],2) + np.power(payload["Az"],2))
    acc_roll = math.atan2(-(payload["Ax"][0]), payload["Az"][0])*180/np.pi
    acc_pitch =  math.atan2(payload["Ay"][0], np.sqrt(np.power(payload["Ax"][0],2) + np.power(payload["Az"][0],2)))*180/np.pi
    gyro_roll = 0 + (payload["Gx"][0]*(payload["d_time"][0]/10000000))
    gyro_pitch = 0 + (payload["Gy"][0]*(payload["d_time"][0]/10000000))
    gyro_yaw = 0 + (payload["Gz"][0]*(payload["d_time"][0]/10000000))
    
    # payload = {"C1":[c1[0]],"C2":[c2[0]]}
    print(acc_roll,acc_pitch)
    payload = {"C1":[c1[0]],"C2":[c2[0]],"Acc_roll":[acc_roll],"Acc_pitch":[acc_pitch],"Gyro_roll":[gyro_roll],"Gyro_pitch":[gyro_pitch],"Gyro_yaw":[gyro_yaw]}
    print(payload)
    post_data = {'dataset_ID': 1, 'date_start': 30,'date_end': 30, 'payload': json.dumps(payload)}
    print(post_data)
    
    y_predict = requests.post('http://127.0.0.1:5000/falls', data=post_data)
    # y_predict = requests.post('http://127.0.0.1:5000/falls', data=post_data).text

    # Make array from the list
    # y_predict = np.array(y_predict)
    print(y_predict.json(), y_predict.status_code)
    
    client.publish('label/machine_learning', json.dumps({'prediction':y_predict.json()['prediction']}))

if __name__ == "__main__":    
    client.on_connect = on_connect    
    client.on_subscribe = on_subscribe    
    client.on_message = on_message    
    client.connect(host="broker.hivemq.com", port=1883)
    
    client.loop_forever()