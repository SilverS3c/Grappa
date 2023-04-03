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
            obj["placheholder"] = "Select a bucket"
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

                    fieldQuery = """import "influxdata/influxdb/schema"

                                    schema.measurementFieldKeys(bucket: "{}", measurement: "{}")""".format(bucket.name, measurement)
                    result = self.client.query_api().query(fieldQuery)
                    for val in result[0]:
                        val = val.values
                        tagobj = {"name": val["_value"], "type": "input", "placeholder": "Filter field"}
                        obj["payloads"].append(tagobj)
                    

            response.append(obj)
        return response



    def loadMetricPayloadOptions(self, req):
        resp = []
        if req["name"] == "_measurement":
            query = f"""
                        import \"influxdata/influxdb/schema\"

                        schema.measurements(bucket: \"{req["metric"]}\")
                        """
            query_api = self.client.query_api()

            tables = query_api.query(query=query, org=self.PLUGIN_CONF["connection"]["org"])
            measurements = [row.values["_value"] for table in tables for row in table]
            
            for measurement in measurements:
                resp.append({"label": measurement, "value": measurement})
            return resp

        # Multiple measurments are possible, and they might have fields with the same name. Maybe querying the field values for all measurements and then merging them? 
        if "metric" in req and "payload" in req and "_measurement" in req["payload"]:
            values = []
            for measurement in req["payload"]["_measurement"]:
                query = f"""import \"influxdata/influxdb/schema\"

                schema.measurementTagValues(bucket: \"{req["metric"]}\", measurement: \"{measurement}\", tag: \"{req["name"]}\")"""

                result = self.client.query_api().query(query)
                for val in result[0]:
                    val = val.values
                    if val["_value"] in values or val["_value"][0] == "_":
                            continue
                    else:
                        values.append(val["_value"])
                        objvalue = {"label": val["_value"], "value": val["_value"]}
                        resp.append(objvalue)
            return resp


    def queryDb(self, request):
        resp = []
        targets = request["targets"]
        for target in targets:
            payload = target["payload"]
            query = "from(bucket: \"{}\") |> range(start: {}, stop: {})".format(target["target"], request["range"]["from"], request["range"]["to"])
            payloadQuery = " |> filter(fn: (r) => {})"
            payloadQueryData = ""
            for key in payload:
                if type(payload[key]) == list:
                    iterations = 0
                    for val in payload[key]:
                        payloadQueryData = payloadQueryData + "r.{} == \"{}\" or ".format(key, val)
                        iterations += 1
                    if iterations > 0:
                        payloadQueryData = payloadQueryData[:-3] + "and "
                else:
                    payloadQueryData = payloadQueryData + "r.{} == \"{}\" and ".format(key, payload[key])
            payloadQueryData = payloadQueryData[:-5]

            if "_measurement" in payload and len(payload["_measurement"]) > 0:
                queryToRun = query + payloadQuery.format(payloadQueryData)
            else:
                queryToRun = query

            print(queryToRun)

            results = self.client.query_api().query(queryToRun)
            respTargets = {}
            for result in results:
                for val in result:
                    print(val)
                    print()
                    val = val.values
                    if val["_field"] not in respTargets:
                        respTargets[val["_field"]] = []
                    respTargets[val["_field"]].append([val["_value"], int(val["_time"].timestamp())*1000])
            
            for obj in respTargets:
                resp.append({"target": obj, "datapoints": respTargets[obj]})
            print(resp)

        return resp