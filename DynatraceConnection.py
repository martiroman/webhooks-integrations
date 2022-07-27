import requests
import time
import datetime
import json

##Clases Dynatrace
class DataPoint(object):
    def __init__(self, tiempo, valor):
        self.timestamp = int(time.mktime(tiempo.timetuple()) * 1000)
        self.valor = valor

    #TODO: Si no es valor numerico
    def formatDataPoint(self):
        return [self.timestamp, float(self.valor)]

class Serie(object):
    def __init__(self, ServiceName, dimensions):
        self.timeseriesId = 'custom:host.service.' + ServiceName.replace(" ", "").lower()
        self.dimensions = { 'metrica' : dimensions }
        self.dataPoints = []
    
    def addDataPoint(self, tiempo, valor):
        dp = DataPoint(tiempo, valor)
        self.dataPoints.append(dp.formatDataPoint())

class Event(object):
    def __init__(self, eventType, title, startTime, endTime, entitySelector):
        self.eventType = eventType
        self.title = title
        #Si es null toma la hora actual
        #self.startTime = startTime
        #self.endTime = endTime
        #The timeout will automatically be capped to a maximum of 300 minutes (5 hours). Problem-opening events can be refreshed and therefore kept open by sending the same payload again. 
        self.timeout = 300
        self.entitySelector ="type(CUSTOM_DEVICE),entityName(" + entitySelector + ")" 
        self.properties = {}

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
        
#"properties" : { "myProperty" : "anyvalue", "myTestProperty2" : "anyvalue"
# "hostNames": [ "coffee-machine.dynatrace.internal.com" ]                        
class CustomHost(object):
    def __init__(self, displayName, ipAdresses, listenPorts, type, favicon, configUrl, grupo):
        self.displayName = displayName
        self.ipAdresses = [ipAdresses]
        self.listenPorts = listenPorts
        self.type = type
        self.favicon = favicon
        self.configUrl = configUrl
        self.series = []
        self.tags = []
        self.group = grupo
        self.properties = { "'ip' : " + ipAdresses }

    def addSerie(self, servicename, metrica, valor):
        dt = datetime.datetime.now()
        serie = Serie(servicename, metrica)
        serie.addDataPoint(dt, valor)
        self.series.append(serie)

    def addTag(self, value):
        self.tags = value

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DynatraceConnection(object):
    def __init__(self):
        self.lstHosts = []
        self.lstEvents = []

    def addCustomHost(self, name, address, puerto, type, favicon, configUrl, grupo):
        dHost = CustomHost(name, address, puerto, type, favicon, configUrl, grupo)
        self.lstHosts.append(dHost)
        return dHost
    
    def addEvent(self, eventType, title, startTime, endTime, entitySelector):
        dEvent = Event(eventType, title, startTime, endTime, entitySelector)
        self.lstEvents.append(dEvent)
            
    def checkIfEvent(self, hostName, serviceName, state):
        dt = datetime.datetime.now()
        timestamp = int(time.mktime(dt.timetuple()) * 1000)
        titulo = "Alerta: " + serviceName
        selector = "type(HOST),entityName(" + hostName + "))"
        encontrado = False

        for event in self.lstEvents:
            if event.entitySelector == selector and event.title == titulo:
                encontrado = True

        if encontrado == True:
            #Si el evento tiene ACK enviar el Cierre a Dynatrace  
            if state == 0:
                print("eliminar evento")
        else:
            if state > 0:   
                #Si el evento tiene ACK enviar el Cierre a Dynatrace              
                self.addEvent("CUSTOM_ALERT", titulo, timestamp, 0, hostName)
            
    def sendMetrics(self):
        for host in self.lstHosts:
            r = requests.post(DT_API_URL + '/api/v1/entity/infrastructure/custom/' + host.displayName + '?Api-Token=' + DT_API_TOKEN, json=json.loads(host.toJson()))
            print("\n PAYLOAD: ")
            print(json.loads(host.toJson()))
            print(host.displayName +": " + r.text + " | " + r.reason)

    def sendEvents(self):
        for event in self.lstEvents:
            r = requests.post(DT_API_URL + '/api/v2/events/ingest?Api-Token=' + DT_API_TOKEN, json=json.loads(event.toJson()))
            print("\n PAYLOAD: ") 
            print(json.loads(event.toJson()))
            print(event.entitySelector + " | " + event.title + " | " + r.text)
            
    def createMetric():
        #TODO: Crear metrica en Dyna
        '''Pendiente'''