from fall_mqtt import FallMQTT
import paho.mqtt.client as mqtt

if __name__ == "__main__":    
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    # api_key = "AIzaSyCIBBs236c9A0tyO6nTpbD6wWFamWIDyYA"
    
    fall = FallMQTT()
    client.on_connect = fall.on_connect    
    client.on_subscribe = fall.on_subscribe    
    client.on_message = fall.on_message    
    client.connect(host="broker.hivemq.com", port=1883)
    
    client.loop_forever()