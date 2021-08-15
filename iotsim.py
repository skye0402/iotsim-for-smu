import paho.mqtt.client as mqtt
import ssl
import time
import random # to get some 'realistic numbers' :-)

# Parameters
sapIotDeviceID = "<your device alternate ID>"
pemCertFilePath = "./certificates/newcert.pem"
mqttServerUrl = "xyzabc.eu10.cp.iot.sap" # enter the IoT cockpit url here
mqttServerPort = 8883 # Port used by SAP IoT
ackTopicLevel = "ack/" 
measuresTopicLevel = "measures/"

# dummy message
dummyMsg = '{{ "capabilityAlternateId": "<your id>", "sensorAlternateId": "<your sensor id>", "measures": [{{"speed": "{}"}}] }}'

# This function gives a connection response from the server
def onConnect(client, userdata, flags, rc):
    rcList = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused",
    }
    print(rcList.get(rc, "Unknown server connection return code {}.".format(rc)))

# The callback for when a PUBLISH message is received from the server.
def onMessage(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

# Send message to SAP MQTT Server
def sendMessage(client, deviceID, messageContentJson):
    time.sleep(random.randint(0,2)) #Wait some random time to make it look realistic
    client.publish(deviceID, messageContentJson)

print("Starting up...")
client = mqtt.Client(sapIotDeviceID) 
client.on_connect = onConnect
client.on_message = onMessage
client.tls_set(certfile=pemCertFilePath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
client.connect(mqttServerUrl, mqttServerPort)
client.subscribe(ackTopicLevel+sapIotDeviceID) #Subscribe to device ack topic (feedback given from SAP IoT MQTT Server)
client.loop_start() #Listening loop start 

for _ in range(10): # We send 10 random values
    sendMessage(client, measuresTopicLevel+sapIotDeviceID, dummyMsg.format(random.randint(10,50)))
time.sleep(2) # wait until we have all feedback messages from the server
client.loop_stop