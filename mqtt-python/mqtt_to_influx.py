import os
import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


broker = "broker.hivemq.com"        
port = 1883
topic_data = "invernadero/sensor/datos"    
mqtt_client_id = "esp32_to_influx"  


url = os.getenv("INFLUX_URL", "http://influxdb:8086")       
token = os.getenv("INFLUX_TOKEN")               
org = os.getenv("INFLUX_ORG")                    
bucket = os.getenv("INFLUX_BUCKET")  
db_client = InfluxDBClient(url=url, token=token, org=org)
write_api = db_client.write_api(write_options=SYNCHRONOUS)


def on_connect_callback(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT, suscribiendo al tema '{topic_data}'...")
    client.subscribe(topic_data)


def on_message_callback(client, userdata, message):
    print("Message received: " + str(message.payload))
    payload = message.payload
    try:
        data = json.loads(payload)
        temp = data.get("temp", None)
        hum = data.get("hum", None)
        luz = data.get("luz", None)
        modo = data.get("modo", None)
        motor = data.get("motor", None)

        if temp is not None and hum is not None and luz is not None:
            point = (
                Point("iot")
                .field("temp", float(temp))
                .field("hum", float(hum))
                .field("luz", float(luz))
                .tag("modo", modo)
                .field("motor", int(motor))
            )
            write_api.write(bucket=bucket, org=org, record=point)

    except ValueError:
        print("Decoding JSON has failed")
    except Exception as e:
        print(f"InfluxDb writing failed: {e}")


def main():
    mqtt_client = mqtt.Client(client_id=mqtt_client_id)     
    mqtt_client.on_connect = on_connect_callback
    mqtt_client.on_message = on_message_callback                   

    print("Connecting to MQTT broker")
    mqtt_client.connect(broker,port,60)                     
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
