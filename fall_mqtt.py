#m.py
import paho.mqtt.client as mqtt
import requests
import json

client = mqtt.Client(protocol=mqtt.MQTTv311)
key = "AIzaSyCIBBs236c9A0tyO6nTpbD6wWFamWIDyYA"

def on_connect(client, userdata, flags, rc):    
    print("Result from connect: {}".format(mqtt.connack_string(rc)))    
    # Subscribe to the senors/alitmeter/1 topic filter 
    client.subscribe("arduino/falls")                                 

def on_subscribe(client, userdata, mid, granted_qos):    
    print("I've subscribed")

def on_message(client, userdata, msg):    
    print("Message received. Topic: {}. Payload: {}".format(
        msg.topic, str(msg.payload)))
    
    payload = eval(msg.payload)
    
    post_data = {'dataset_ID': 1, 'date_start': 30,'date_end': 30, 'payload': json.dumps(payload)}
    
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