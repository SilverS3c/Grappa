from flask import Flask, jsonify, request
import json
import sys
import argparse
import logging
import logging.handlers
import importlib
import os

class GrappaLogging:
    class Type:
        REQUEST = "Request"
        RESPONSE = "Response"

    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    logger = None
    def init(filename, format, level, appid, plugin, rotationConfig):
        if format.lower() == "json":
            template = '{"level": "%(levelname)s", "time": "%(asctime)s",' + ' "app": "{}"'.format(appid) + ', "type": "%(type)s", ' + '"plugin": "{}", "msg": "%(message)s"'.format(plugin) + ', "method": "%(method)s", "endpoint": "%(endpoint)s"}'
        else:
            template = 'level=%(levelname)s, time=%(asctime)s, app={}, type=%(type)s, plugin={}, method=%(method)s, endpoint=%(endpoint)s, msg=%(message)s'.format(appid, plugin)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        GrappaLogging.logger = logging.getLogger("Grappa")
        GrappaLogging.logger.setLevel(GrappaLogging.parseLogLevel(level))
        
        ch = logging.StreamHandler()
        ch.setLevel(GrappaLogging.parseLogLevel(level))
        formatter = logging.Formatter(template, "%Y-%m-%dT%H:%M:%S%zZ")
        
        ch.setFormatter(formatter)
        if rotationConfig["active"].lower() == "size" and rotationConfig["size"] != 0 and rotationConfig["size"] != "0" and rotationConfig["size"] != "":
            sizehandler = logging.handlers.RotatingFileHandler(filename, maxBytes=GrappaLogging.convertSize(rotationConfig["size"]), backupCount=rotationConfig["backupCount"])
            sizehandler.setLevel(GrappaLogging.parseLogLevel(level))
            GrappaLogging.logger.addHandler(sizehandler)
        elif rotationConfig["active"].lower() == "time" and rotationConfig["time"] != 0:
            timeHandler = logging.handlers.TimedRotatingFileHandler(filename, when="d", interval=rotationConfig["time"], backupCount=rotationConfig["backupCount"])
            timeHandler.setLevel(GrappaLogging.parseLogLevel(level))
            GrappaLogging.logger.addHandler(timeHandler)
        else:
            fh = logging.FileHandler(filename)
            fh.setLevel(GrappaLogging.parseLogLevel(level))
            fh.setFormatter(formatter)
            GrappaLogging.logger.addHandler(fh)
        
        
        GrappaLogging.logger.addHandler(ch)
        
    
    def parseLogLevel(level):
        return GrappaLogging.levels[level.lower()]
    
    def getLogger():
        return GrappaLogging.logger
    
    def convertSize(size):
        parse = {
            "b": 1,
            "kb": 1000,
            "k":  1000,
            "mb": 1000**2,
            "m":  1000**2,
            "gb": 1000**3,
            "g":  1000**3,
            "tb": 1000**4
        }
        sizeText = ""
        for char in size:
            if ord(char) < 48 or ord(char) > 57:    #ASCII 48 = '0', 57 = '9'
                sizeText += char
        if sizeText == "":
            sizeText = "b"
        try:
            return int(size[:-len(sizeText)]) * parse[sizeText.lower()]
        except Exception as e:
            GrappaLogging.getLogger().error(e, extra={"type": "", "method": "", "endpoint": "/query"})


class Grappa:
    def __init__(self, CONFIG, PLUGIN_CONF, pluginPath, instanceId, pluginName):
        self.CONFIG = CONFIG
        self.PLUGIN_CONF = PLUGIN_CONF
        self.instanceId = instanceId
        GrappaLogging.init(CONFIG["log"]["file"], CONFIG["log"]["format"], CONFIG["log"]["level"], instanceId, pluginName, CONFIG["log"]["rotation"])
        self.plugin = importlib.import_module(pluginPath, ".").Plugin(CONFIG, PLUGIN_CONF, GrappaLogging.getLogger())
        
        

    def healthCheck(self):
        GrappaLogging.getLogger().info("", extra={"type": GrappaLogging.Type.REQUEST, "method": request.method, "endpoint": request.path})
        return ""

    def metrics(self):
        GrappaLogging.getLogger().info("", extra={"type": GrappaLogging.Type.REQUEST, "method": request.method, "endpoint": request.path})
        metrics = self.plugin.getMetrics(request.get_json())
        return metrics

    def metricPayloadOptions(self):
        GrappaLogging.getLogger().info("", extra={"type": GrappaLogging.Type.REQUEST, "method": request.method, "endpoint": request.path})
        return self.plugin.loadMetricPayloadOptions(request.get_json())

    def query(self):
        GrappaLogging.getLogger().info("", extra={"type": GrappaLogging.Type.REQUEST, "method": request.method, "endpoint": request.path})
        result = self.plugin.queryDb(request.get_json())
        return result
    

def loadMainConfig(path="./config/main.json"):
        with open(path, "r") as conf:
            return json.load(conf)

CONFIG = loadMainConfig()

argparser = argparse.ArgumentParser(description="python3 grappa.py -b/--backend <plugin> -i/--id <app identifier>")
argparser.add_argument("--backend", "-b", choices=[plugin["name"] for plugin in CONFIG["plugins"]], nargs=1, required=True, type=str)
argparser.add_argument("--id", "-i", nargs=1, required=True, type=str)
args = argparser.parse_args()
    
def loadPluginConfig():
        for plugin in CONFIG["plugins"]:
            if plugin["name"] == args.backend[0]:
                with open(plugin["config"]) as f:
                    return json.load(f)
        raise Exception("No plugin found with specified name!")

PLUGIN_CONF = loadPluginConfig()

def getPluginPath():
    for plugin in CONFIG["plugins"]:
        if plugin["name"] == args.backend[0]:
            return plugin["file"]
    raise Exception("No plugin found!")
            
grappa = Grappa(CONFIG, PLUGIN_CONF, getPluginPath(), args.id[0], args.backend[0])

app = Flask(__name__)

@app.route("/")
def healthCheck():
     return grappa.healthCheck()

@app.route("/metrics", methods=['POST'])
def metrics():
    return grappa.metrics()

@app.route('/metric-payload-options', methods = ['POST'])
def metricPayloadOptions():
    return grappa.metricPayloadOptions()

@app.route('/query', methods = ['POST'])
def query():
    return grappa.query()

if __name__ == '__main__':
    app.run(host=CONFIG["listen"]["address"], port=CONFIG["listen"]["port"], debug=True)