#m.py
import paho.mqtt.client as mqtt
import numpy as np
import requests
import json
import math
from Kalman import KalmanAngle

class FallMQTT():

    def __init__(self):
        
        self.kalmanZ = KalmanAngle()
        self.kalmanX = KalmanAngle()
        self.kalAngleZ = 0
        self.kalAngleX = 0
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
    
    def calculate_Kalman(self, accRoll, accPitch, gX, gY, gZ, dTime):
        compConst = 1/(1+dTime)
        
        yaw = self.yaw +(gY*dTime)
        if yaw < 0:
            yaw = yaw+360.0
            
        self.kalmanZ.setAngle(accRoll)
        self.kalmanX.setAngle(accPitch)
        
        gyroZAngle = accRoll
        gyroXAngle = accPitch
        # compAngleZ = accRoll
        # compAngleX = accPitch   
        
        gyroZRate = gZ
        gyroXRate = gX
        
        if((accRoll < -90 and kalAngleX >90) or (accRoll > 90 and kalAngleX < -90)):
            self.kalmanZ.setAngle(accRoll)
            # complAngleZ = accRoll
            kalAngleX   = accRoll
            gyroZAngle  = accRoll
        else:
            kalAngleZ = self.kalmanZ.getAngle(accRoll,gyroZRate,dTime)

        if(abs(kalAngleZ)>90):
            gyroXRate  = -gyroXRate
            kalAngleX  = self.kalmanX.getAngle(accPitch,gyroXRate,dTime)
        
        gyroZAngle = gyroZRate * dTime
        gyroXAngle = gyroXAngle * dTime

        #compAngle = constant * (old_compAngle + angle_obtained_from_gyro) + (1-constant) * angle_obtained from accelerometer
        # compAngleZ = compConst * (compAngleZ + gyroZRate * dTime) + (1-compConst) * accRoll
        # compAngleX = compConst * (compAngleX + gyroXRate * dTime) + (1-compConst) * accPitch

        if ((gyroZAngle < -180) or (gyroZAngle > 180)):
            gyroZAngle = kalAngleZ
        if ((gyroXAngle < -180) or (gyroXAngle > 180)):
            gyroXAngle = kalAngleX
        
        self.roll = kalAngleZ
        self.pitch = kalAngleX
        self.yaw = yaw
        
        return True

    def on_connect(client, userdata, flags, rc):    
        print("Result from connect: {}".format(mqtt.connack_string(rc)))    
        # Subscribe to the arduino/falls topic filter 
        client.subscribe("arduino/falls")                                 

    def on_subscribe(client, userdata, mid, granted_qos):    
        print("I've subscribed")

    def on_message(self, client, userdata, msg):    
        print("Message received. Topic: {}. Payload: {}".format(
            msg.topic, str(msg.payload)))
        
        payload = eval(msg.payload)
        
        rad_to_deg = 180/np.pi
        
        c1 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Az"],2))
        c2 = np.sqrt(np.power(payload["Ax"],2) + np.power(payload["Ay"],2) + np.power(payload["Az"],2))
        acc_roll = math.atan2(payload["Az"][0], payload["Ay"][0])*rad_to_deg
        acc_pitch =  math.atan(-(payload["Ax"][0])/(np.sqrt(np.power(payload["Az"][0],2) + np.power(payload["Ay"][0],2))))*rad_to_deg
        
        if(self.calculate_Kalman(acc_roll,acc_pitch,payload["Gx"][0],payload["Gy"][0],payload["Gz"][0],payload["d_time"][0])):
            print("Roll, Pitch, Yaw fusioned!")
        else:
            print("Fusion failed!")
        
        # payload = {"C1":[c1[0]],"C2":[c2[0]]}
        # print(acc_roll,acc_pitch)
        payload = {"C1":[c1[0]],"C2":[c2[0]],"Roll":[self.roll],"Pitch":[self.pitch],"Yaw":[self.yaw]}
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
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    api_key = "AIzaSyCIBBs236c9A0tyO6nTpbD6wWFamWIDyYA"
    
    fall = FallMQTT()
    client.on_connect = fall.on_connect    
    client.on_subscribe = fall.on_subscribe    
    client.on_message = fall.on_message    
    client.connect(host="broker.hivemq.com", port=1883)
    
    client.loop_forever()