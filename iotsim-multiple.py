import paho.mqtt.client as mqtt
import ssl
import time
import re
import random # to get some 'realistic numbers' :-)
import configparser
from datetime import datetime

iotDevMessage = '{{ "capabilityAlternateId": "simpleCapability", "sensorAlternateId": "simpleSensor", "measures": [{{"temperature": "{}"}}] }}'

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
        print(msg.topic + " " + str(msg.payload))

    # Subscription to topic confirmation
    def onSubscribe(self,client, userdata, mid, granted_qos):
        pass

    # object constructor
    def __init__(self, certFilename, pemCertFilePath, url, port, ack, measure):
        super().__init__()
        n = 3 # Cut after 3rd "-"
        deviceName=re.match(r'^((?:[^-]*-){%d}[^-]*)-(.*)' % (n-1), certFilename)
        if deviceName: 
            self.id = deviceName.groups()[0]
            self.teamno = re.findall('\d+', self.id)[0]
            self.url = url
            self.port = port
            self.ack = ack
            self.measure = measure
            self.ackid = self.ack+self.id
            self.client = mqtt.Client(self.id) 
            self.client.on_connect = self.onConnect
            self.client.on_message = self.onMessage
            self.client.on_subscribe = self.onSubscribe
            self.client.tls_set(certfile=pemCertFilePath+certFilename, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)

    # connect method for the device object
    def connect(self):
        self.client.connect(self.url, self.port)
        self.client.loop_start() #Listening loop start 

    # Send message to SAP MQTT Server
    def sendMessage(self, messageContentJson):
        time.sleep(random.randint(0,2)) #Wait some random time to make it look realistic
        messageInfo = self.client.publish(self.measure+self.id, messageContentJson)
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

def endless_loop(msg):
    print(msg + " Entering endless loop. Check and redo deployment?")
    while True:
        pass

# To interpret configured templates of JSON
def fstr(iotDevice, template):
    return eval(f"f'{template}'")

def main():
    # Parameters
    deviceDictionary = {} # contains all IoT devices

    # Get configuration
    config = configparser.ConfigParser(inline_comment_prefixes="#")
    config.read(['./config/iotsim.cfg'])
    if not config.has_section("server"):
        endless_loop("Config: Server section missing.")
    if not config.has_section("topics"):
        endless_loop("Config: Topics section missing.")
    if not config.has_section("messages"):
        endless_loop("Config: Messages section missing.")
    if not config.has_section("timing"):
        endless_loop("Config: Timing section missing.")             
    # -------------- Parameters ------------------>>>
    mqttServerUrl = config.get("server","mqttServerUrl")
    mqttServerPort = config.getint("server","mqttServerPort")
    pemCertFilePath = config.get("server","pemCertFilePath")
    ackTopicLevel = config.get("topics","ackTopicLevel")
    measuresTopicLevel = config.get("topics","measuresTopicLevel")
    iotDevMessage = config.get("messages","messageTemplate")
    pauseTime = int(config.get("timing","pauseInSeconds"))
    runTime = int(config.get("timing","runtimeOfProgram"))
    # -------------- Parameters ------------------<<<

    # Get Certificate file names
    from os import listdir
    from os.path import isfile, join
    certFilenames = [f for f in listdir(pemCertFilePath) if isfile(join(pemCertFilePath, f))]

    if not certFilenames:
        endless_loop("No certificate files.")
    else:
        print("Starting up...")

    # Build dictionary of and connect devices
    for certFilename in certFilenames:
        deviceObject = IotDevice(certFilename, pemCertFilePath, mqttServerUrl, mqttServerPort, ackTopicLevel, measuresTopicLevel)
        deviceDictionary[deviceObject.getId] = deviceObject
        deviceObject.connect()
    time.sleep(2)

    loopCondition = True
    then = datetime.now()

    # Start sending data to cloud
    while loopCondition:
        for deviceId in list(deviceDictionary):
            deviceDictionary[deviceId].sendMessage(fstr(deviceDictionary[deviceId], iotDevMessage))
        time.sleep(pauseTime)
        if runTime > 0:
            now = datetime.now()
            durationMins = divmod((now-then).total_seconds(), 60)[0]
            if durationMins > runTime:
                loopCondition = False

    time.sleep(2) # wait until we have all feedback messages from the server
    for deviceId in list(deviceDictionary):
        deviceDictionary[deviceId].stop()

    print("Shut down all clients. Entering endless loop. Restart pod if needed.")
    while True:
        pass

if __name__ == "__main__":
    main()