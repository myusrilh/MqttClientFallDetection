#m.py
import paho.mqtt.client as mqtt
import numpy as np
import requests
import json
import math
import time, datetime
from Kalman import KalmanAngle

class FallMQTT():

    def __init__(self):
        
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        # self.gyr_sen = gyr_sen
        # self.acc_sen = 1/64
    
    def calculate_complementary(self, accRoll, accPitch, gX, gY, gZ, dTime):
        compConst = 1/(1+dTime)
        self.roll = 0 + ((gZ*dTime)*compConst) + (accRoll*(1-compConst))
        self.pitch = 0 + ((gX*dTime)*compConst) + (accPitch*(1-compConst))
        
#             dataframe.loc[ind,"Yaw"] = dataframe.loc[ind,"Yaw"]+ (dataframe.loc[ind,"Gy"]*d_time)
        self.yaw = 0 + (gY*dTime)
        if self.yaw < 0:
            self.yaw = self.yaw + 360.0
        
        # self.roll = roll
        # self.pitch = pitch
        
        return True

    def on_connect(self, client, userdata, flags, rc):    
        print("Result from connect: {}".format(mqtt.connack_string(rc)))    
        # Subscribe to the arduino/falls topic filter 
        client.subscribe("arduino/falls")                                 

    def on_subscribe(self, client, userdata, mid, granted_qos):    
        print("I've subscribed")

    def on_message(self, client, userdata, msg):    
        print("Message received. Topic: {}. Payload: {}".format(
            msg.topic, str(msg.payload)))
        
        payload = eval(msg.payload)
        
        rad_to_deg = 180/np.pi
        # d_time = 1/238
        
        c1 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Az"],2))
        c2 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Ay"],2) + np.power(payload["Az"],2))
        acc_roll = math.atan2(payload["Az"][0], payload["Ay"][0])*rad_to_deg
        acc_pitch =  math.atan2((payload["Ax"][0]),(np.sqrt(np.power(payload["Az"][0],2) + np.power(payload["Ay"][0],2))))*rad_to_deg
        
        dTime = payload["d_time"][0]
        # if(self.calculate_Kalman(acc_roll,acc_pitch,payload["Gx"][0],payload["Gy"][0],payload["Gz"][0],payload["d_time"][0])):
        gX = payload["Gx"][0]
        gY = payload["Gy"][0]
        gZ = payload["Gz"][0]
        
        if(self.calculate_complementary(acc_roll,acc_pitch,gX,gY,gZ,dTime)):
            print("Roll, Pitch, Yaw fusioned!")
            print("{\"Roll\":["+str(self.roll)+"],\"Pitch\":["+str(self.pitch)+"],\"Yaw\":["+str(self.yaw)+"]}")
        else:
            print("Fusion failed!")
        
        # payload = {"C1":[c1[0]],"C2":[c2[0]]}
        # print(acc_roll,acc_pitch)
        payload = {"C1":[c1[0]],"C2":[c2[0]],"Roll":[self.roll],"Pitch":[self.pitch],"Yaw":[self.yaw]}
        # print(payload)
        post_data = {'dataset_ID': 1, 'time': json.dumps(dTime), 'payload': json.dumps(payload)}
        # print(post_data)
        
        # dt_before_req_api = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M:%S.%f")
        dt_before_req_api = time.strftime('%A, %d %B %Y %H:%M:%S')
        
        y_predict = requests.post('http://127.0.0.1:5000/falls', data=post_data)
        
        # dt_after_req_api = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M:%S.%f")
        dt_after_req_api = time.strftime('%A, %d %B %Y %H:%M:%S')
        
        # y_predict = requests.post('http://127.0.0.1:5000/falls', data=post_data).text

        # Make array from the list
        # y_predict = np.array(y_predict)
        # client.publish('label/machine_learning', json.dumps({'prediction':y_predict.json()['prediction'],'seconds':y_predict.json()['seconds'],'datetime':y_predict.json()['datetime']}))
        client.publish('label/machine_learning', json.dumps({'prediction':y_predict.json()['prediction'],'dt_after_pred':y_predict.json()['dt_after_pred'],'dt_before_pred':y_predict.json()['dt_before_pred']}))
        
        # logFile = open('log-pred.txt','a') #a = append, rw = read/write, w = write
        # logFile.write("\n"+dt_before_req_api+", "+dt_after_req_api+", "+y_predict.json()['dt_before_pred']+", "+y_predict.json()['dt_after_pred']+", "+y_predict.json()['prediction']+", "+str(y_predict.status_code))
        
        print("\nResult: ",y_predict.json())
        print("\tStatus code:",y_predict.status_code)
        
