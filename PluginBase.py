from jsonschema import validate
import json

class PluginBase:
    def __init__(self, CONFIG, PLUGIN_CONF, logger) -> None:
        self.CONFIG = CONFIG
        self.PLUGIN_CONF = PLUGIN_CONF
        self.logger = logger

    def getMetrics(self, request):
        pass

    def loadMetricPayloadOptions(self, req):
        pass

    def queryDb(self, request):
        pass

    def validateConfig(self, pluginName: str):
        for plugin in self.CONFIG["plugins"]:
            if plugin["name"] == pluginName:
                schemaPath = '/'.join(plugin["config"].split('/')[:-1]) + "/" + self.PLUGIN_CONF["$schema"]
        
        print(schemaPath)
        schema = None
        with open(schemaPath, 'r') as f:
            schema = f.read()
        schema = json.loads(schema)
        print(schema)
        validate(self.PLUGIN_CONF, schema)