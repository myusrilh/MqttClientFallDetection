#m.py

import time
import paho.mqtt.client as mqtt
import numpy as np
import requests
import json
import math
from datetime import datetime
from dateutil import parser

from sqlalchemy import null

class FallMQTT():

    def __init__(self):
        
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.jatuh = False
        self.posisiLantai = False
        self.countJatuh = 0
        # self.start = round(time.time()*1000)
        self.start = 0
        self.end = 0
        self.cond = ""
        self.alert = ""
    
    def calculate_complementary(self, accRoll, accPitch, gX, gY, gZ, dTime):
        const_time = 2
        compConst = const_time/(const_time+dTime)
        self.roll = 0 + ((gZ*dTime)*compConst) + (accRoll*(1-compConst))
        self.pitch = 0 + ((gX*dTime)*compConst) + (accPitch*(1-compConst))
        
        self.yaw = 0 + (gY*dTime)
        if self.yaw < 0:
            self.yaw = self.yaw + 360.0
        
        
        if self.yaw != 0 and self.roll != 0 and self.pitch !=0:
            return True
        else:
            return False

    def on_connect(self, client, userdata, flags, rc):    
        print("Result from connect: {}".format(mqtt.connack_string(rc)))    
        # Subscribe to the arduino/falls topic filter 
        client.subscribe("arduino/falls")                                 

    def on_subscribe(self, client, userdata, mid, granted_qos):    
        print("I've subscribed")

    def on_message(self, client, userdata, msg):    
        # print("Message received. Topic: {}. Payload: {}".format(
        #     msg.topic, str(msg.payload)))
        
        if msg is not null:
            payload = eval(msg.payload)
        else:
            payload = {"Ax":[0.01],"Ay":[0.01],"Az":[0.01],"Gx":[0.1],"Gy":[0.1],"Gz":[0.1],"d_time":[0.009]}
        
        longitude = payload["longitude"]
        latitude = payload["latitude"]
        
        rad_to_deg = 180/np.pi
        
        c1 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Az"],2))
        c2 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Ay"],2) + np.power(payload["Az"],2))
        acc_roll = math.atan2(-(payload["Az"][0]), payload["Ay"][0])*rad_to_deg
        acc_pitch =  math.atan2((payload["Ax"][0]),(np.sqrt(np.power(payload["Az"][0],2) + np.power(payload["Ay"][0],2))))*rad_to_deg
        
        dTime = payload["d_time"][0]
        
        gX = payload["Gx"][0]
        gY = payload["Gy"][0]
        gZ = payload["Gz"][0]
        
        if(self.calculate_complementary(acc_roll,acc_pitch,gX,gY,gZ,dTime)):
            print("Roll, Pitch, Yaw fusioned!")
            # print("{\"Roll\":["+str(self.roll)+"],\"Pitch\":["+str(self.pitch)+"],\"Yaw\":["+str(self.yaw)+"]}")
        else:
            print("Fusion failed!")
        
        
        data = {"C1":[c1[0]],"C2":[c2[0]],"Roll":[self.roll],"Pitch":[self.pitch],"Yaw":[self.yaw]}
        # payload = {"Ax":[payload["Ax"][0]],"Ay":[payload["Ay"][0]],"Az":[payload["Az"][0]],"Gx":[gX],"Gy":[gY],"Gz":[gZ],"C1":[c1[0]],"C2":[c2[0]]}
        
        post_data = {'dataset_ID': 1, 'time': dTime, 'payload': json.dumps(data)}
        
        dt_before_req_api = datetime.utcnow().isoformat(sep=' ', timespec='milliseconds')
        
        y_predict = requests.post('http://127.0.0.1:5000/falls', data=post_data) #localhost
        # y_predict = requests.post('https://falldetectionsystemapi.herokuapp.com/falls', json=post_data) #heroku
        
        dt_after_req_api = datetime.utcnow().isoformat(sep=' ', timespec='milliseconds')
        print(y_predict)
        client.publish('label/machine_learning', json.dumps({"prediction":y_predict.json()['prediction'],"dt_after_pred":y_predict.json()['dt_after_pred'],'dt_before_pred':y_predict.json()['dt_before_pred'],'lat':payload['latitude'][0],'lon':payload['longitude'][0]}))
        
        logFile = open('log-pred.txt','a') #a = append, rw = read/write, w = write
        
        
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Walking")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Standing")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Jogging")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Fall forward")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Fall backward")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Sit down")
        # logFile.write("\n"+dt_before_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+","+dt_after_req_api+", "+cond+", "+str(y_predict.status_code)+", Lie down")
        
        print("\nResult: ",y_predict.json())
        print("\tStatus code:",y_predict.status_code)
        
if __name__ == "__main__":    
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    
    fall = FallMQTT()
    
    client.on_connect = fall.on_connect    
    client.on_subscribe = fall.on_subscribe    
    client.on_message = fall.on_message    
    client.connect(host="broker.hivemq.com", port=1883)
    
    client.loop_forever()
