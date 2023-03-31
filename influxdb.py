from PluginBase import PluginBase
import influxdb_client
from flask import request
import json

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

            
            measurements_obj = {"name": "measurement", "type": "multi-select", "placeholder": "Select a measurement", "reloadMetric": True}

            obj["payloads"].append(measurements_obj)

            if "metric" in request and "payload" in request and "measurement" in request["payload"]:
                # add tags and fields
                tags = []
                for measurement in request["payload"]["measurement"]:
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

            response.append(obj)
        return response



    def loadMetricPayloadOptions(self, req):
        resp = []
        if req["name"] == "measurement":
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
        if "metric" in req and "payload" in req and "measurement" in req["payload"]:
            values = []
            for measurement in req["payload"]["measurement"]:
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
        return []