import paho.mqtt.client as mqtt
import ssl
import time
import re
import random # to get some 'realistic numbers' :-)

pemCertFilePath = "./certificates/"
mqttServerUrl = "a4042ecf-281e-4d4a-b721-c9b43461e188.eu10.cp.iot.sap" # enter the IoT cockpit url here
mqttServerPort = 8883 # Port used by SAP IoT
ackTopicLevel = "ack/" 
measuresTopicLevel = "measures/"
dummyMsg = '{{ "capabilityAlternateId": "simpleCapability", "sensorAlternateId": "simpleSensor", "measures": [{{"temperature": "{}"}}] }}'

class IotDevice:
    # class variables

    # class methods

    # This function gives a connection response from the server
    def onConnect(self, client, userdata, flags, rc):
        rcList = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused",
        }
        print(rcList.get(rc, "Unknown server connection return code {}.".format(rc)))
        (result, mid) = self.client.subscribe(self.ackid) #Subscribe to device ack topic (feedback given from SAP IoT MQTT Server)
        print("Subscribed to "+self.ackid+" with result: "+str(result)+" request #"+str(mid))

    # The callback for when a PUBLISH message is received from the server.
    def onMessage(self, client, userdata, msg):
        print("Hello")
        print(msg.topic + " " + str(msg.payload))

    # Subscription to topic confirmation
    def onSubscribe(self,client, userdata, mid, granted_qos):
        pass

    # object constructor
    def __init__(self, certFilename):
        super().__init__()
        n = 3 # Cut after 3rd "-"
        deviceName=re.match(r'^((?:[^-]*-){%d}[^-]*)-(.*)' % (n-1), certFilename)
        if deviceName: 
            self.id = deviceName.groups()[0]
            self.ackid = ackTopicLevel+self.id
            self.client = mqtt.Client(self.id) 
            self.client.on_connect = self.onConnect
            self.client.on_message = self.onMessage
            self.client.on_subscribe = self.onSubscribe
            self.client.tls_set(certfile=pemCertFilePath+certFilename, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            self.client.connect(mqttServerUrl, mqttServerPort)
            self.client.loop_start() #Listening loop start 
            self.client.publish(self.id, dummyMsg.format(random.randint(10,50) ))
            #self.sendMessage(dummyMsg.format(random.randint(10,50)))

    # connect method for the device object
    def connect(self):
        pass

    # Send message to SAP MQTT Server
    def sendMessage(self, messageContentJson):
        time.sleep(random.randint(0,2)) #Wait some random time to make it look realistic
        messageInfo = self.client.publish(self.id, messageContentJson)
        print(messageContentJson)
        print("Sent message for " + self.id + " with result " + str(messageInfo.rc) + " request #" + str(messageInfo.mid))

    # Stop the client
    def stop(self):
        self.client.loop_stop
        print("Shut down device "+self.id)

    # object destructor
    #def __del__(self):
        # No code yet       

    def getId(self):
        return self.id


def main():
    # Parameters
    deviceDictionary = {} # contains all IoT devices

    # Get Certificate file names
    from os import listdir
    from os.path import isfile, join
    certFilenames = [f for f in listdir(pemCertFilePath) if isfile(join(pemCertFilePath, f))]

    print("Starting up...")

    # Build dictionary of and connect devices
    for certFilename in certFilenames:
        deviceObject = IotDevice(certFilename)
        deviceDictionary[deviceObject.getId] = deviceObject
        deviceObject.connect()

    # Start sending data to cloud
    time.sleep(10)
    for _ in range(2): # We send 2 random values
        for deviceId in list(deviceDictionary):
            deviceDictionary[deviceId].sendMessage(dummyMsg.format(random.randint(10,50)))

    time.sleep(2) # wait until we have all feedback messages from the server
    for deviceId in list(deviceDictionary):
        deviceDictionary[deviceId].stop()

if __name__ == "__main__":
    main()