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