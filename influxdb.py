from PluginBase import PluginBase
import influxdb_client
from flask import request
import json
import time
import datetime
from dateutil.tz import tzutc

class Plugin(PluginBase):
    def __init__(self, CONFIG, PLUGIN_CONF, logger) -> None:
        self.CONFIG = CONFIG
        self.PLUGIN_CONF = PLUGIN_CONF
        self.logger = logger
        self.client = influxdb_client.InfluxDBClient(self.PLUGIN_CONF["connection"]["address"],
                                                    self.PLUGIN_CONF["connection"]["token"],
                                                    org=self.PLUGIN_CONF["connection"]["org"])

    def getMetrics(self, request):
        response = []
        buckets = self.client.buckets_api().find_buckets()
        for bucket in buckets.buckets:
            if bucket.name[0] == '_':
                continue
            obj = {}
            obj["value"] = bucket.name
            obj["placeholder"] = "Select a bucket"
            obj["payloads"] = []

            measurements_obj = {"name": "_measurement", "type": "multi-select", "placeholder": "Select a measurement", "reloadMetric": True}

            obj["payloads"].append(measurements_obj)

            if "metric" in request and "payload" in request and "_measurement" in request["payload"]:
                # add tags and fields
                tags = []
                for measurement in request["payload"]["_measurement"]:
                    key_query = """
                    import "influxdata/influxdb/schema"

                    schema.measurementTagKeys(bucket: "{}", measurement: "{}")
                    """.format(bucket.name, measurement)
                    result = self.client.query_api().query(key_query)
                    
                    for val in result[0]:
                        val = val.values
                        if val["_value"] in tags or val["_value"][0] == "_":
                            continue
                        else:
                            tags.append(val["_value"])
                            tagobj = {"name": val["_value"], "type": "multi-select", "placeholder": "Select tag"}
                            obj["payloads"].append(tagobj)

                    obj["payloads"].append({"name": "_field", "type": "multi-select", "placeholder": "Select the fields"})
                    obj["payloads"].append({"name": "_value", "type": "input", "placeholder": "Filter the values"})
                    
                    
            response.append(obj)
        return response


    def loadMetricPayloadOptions(self, req):
        resp = []
        if req["name"] == "_measurement":
            measurements = self.queryMeasurements(req)
            
            for measurement in measurements:
                resp.append({"label": measurement, "value": measurement})
            return resp

        if req["name"] == "_field":
            for measurement in req["payload"]["_measurement"]:
                result = self.queryFieldNames(req, measurement)
                for val in result[0]:
                    val = val.values
                    tagobj = {"value": val["_value"], "label": val["_value"]}
                    resp.append(tagobj)
            return resp
        # Multiple measurments are possible, and they might have fields with the same name. Querying the field values for all measurements and merging them 
        if self.isMeasurementSetInReq(req):
            values = []
            for measurement in req["payload"]["_measurement"]:
                result = self.queryTagValues(req, measurement)
                for val in result[0]:
                    val = val.values
                    if val["_value"] in values or val["_value"][0] == "_":
                            continue
                    else:
                        values.append(val["_value"])
                        objvalue = {"label": val["_value"], "value": val["_value"]}
                        resp.append(objvalue)
            return resp
        
    def queryFieldNames(self, req, measurement):
        fieldQuery = """import "influxdata/influxdb/schema"

                    schema.measurementFieldKeys(bucket: "{}", measurement: "{}")""".format(req["metric"], measurement)
        return self.client.query_api().query(fieldQuery)
        
        
    def queryTagValues(self, req, measurement):
        query = f"""import \"influxdata/influxdb/schema\"

            schema.measurementTagValues(bucket: \"{req["metric"]}\", measurement: \"{measurement}\", tag: \"{req["name"]}\")"""
        return self.client.query_api().query(query)
        
    def isMeasurementSetInReq(self, req):
        return "metric" in req and "payload" in req and "_measurement" in req["payload"]
    
    def queryMeasurements(self, req):
        query = f"""
                import \"influxdata/influxdb/schema\"

                schema.measurements(bucket: \"{req["metric"]}\")
                """
        query_api = self.client.query_api()

        tables = query_api.query(query=query, org=self.PLUGIN_CONF["connection"]["org"])
        return [row.values["_value"] for table in tables for row in table]

    def queryDb(self, request):
        resp = []
        targets = request["targets"]
        for target in targets:
            query = "from(bucket: \"{}\") |> range(start: {}, stop: {})".format(target["target"], request["range"]["from"], request["range"]["to"])
            payloadQuery = " |> filter(fn: (r) => {})"
            payload = target["payload"]
            
            payloadQueryData = self.generatePayloadQueryData(payload)

            if self.hasMeasurementSelected(payload):
                queryToRun = query + payloadQuery.format(payloadQueryData)
            else:
                queryToRun = query


            results = self.client.query_api().query(queryToRun)
            respTargets = {}
            self.collectQueryResultsToTempObject(results, respTargets)
            
            for obj in respTargets:
                resp.append({"target": obj, "datapoints": respTargets[obj]})

        return resp
    
    def collectQueryResultsToTempObject(self, results, respTargets):
        for result in results:
            for val in result:
                val = val.values
                valName = self.generateNameFromInfluxObject(val)
                if valName not in respTargets:
                    respTargets[valName] = []
                respTargets[valName].append([val["_value"], int(val["_time"].timestamp())*1000])
    
    def hasMeasurementSelected(self, payload):
        return "_measurement" in payload and len(payload["_measurement"]) > 0
    
    def generatePayloadQueryData(self, payload):
        payloadQueryData = ""
        for key in payload:
            if type(payload[key]) == list:
                payloadQueryData += "("
                iterations = 0
                for val in payload[key]:
                    payloadQueryData = payloadQueryData + "r.{} == \"{}\" or ".format(key, val)
                    iterations += 1
                if iterations > 0:
                    payloadQueryData = payloadQueryData[:-3] + ")" + " and "
                elif iterations == 0:
                    payloadQueryData = payloadQueryData[:-1]
            else:
                # value filtering
                if payload[key][0] == '>' or payload[key][0] == '<':
                    if payload[key][1] == '=':
                        payloadQueryData = payloadQueryData + "r.{} {} {} and ".format(key, payload[key][:2], float(payload[key][2:].strip()))
                    else:
                        payloadQueryData = payloadQueryData + "r.{} {} {} and ".format(key, payload[key][0], float(payload[key][1:].strip()))
                elif payload[key].startswith("!="):
                     payloadQueryData = payloadQueryData + "r.{} != {} and ".format(key, float(payload[key][2:].strip()))
                else:
                    payloadQueryData = payloadQueryData + "r.{} == {} and ".format(key, float(payload[key].strip()))
        return payloadQueryData[:-5]
    
    def generateNameFromInfluxObject(self, obj):
        name = obj["_field"]
        excludeTags = ["result", "table", "_start", "_stop", "_time", "_value", "_field"]
        for tag in obj:
            if tag in excludeTags:
                continue
            name += "_" + obj[tag]
        return name
