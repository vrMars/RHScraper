import os
import time
import paho.mqtt.client as mqtt

def on_message(client, userdata, message):
    msg = str(message.payload.decode("utf-8"))
    output = msg.split(';')
    # print('here : ', output)
    try:
        with open('profits', 'w') as f:
            for l in output:
                if l != '\n':
                    f.write(l)
                    f.write('\n')
    except Exception as e:
        print(e)


broker = '192.168.86.249'

client = mqtt.Client("RHClient")
client.connect(broker)

client.subscribe("rhscraper")
client.on_message=on_message

client.loop_forever()

