from flask import Flask, jsonify, request
import json
import sys
import argparse
import logging
import importlib

class Grappa:
    def __init__(self, CONFIG, PLUGIN_CONF, pluginPath):
        self.CONFIG = CONFIG
        self.PLUGIN_CONF = PLUGIN_CONF
        self.plugin = importlib.import_module(pluginPath, ".").Plugin(CONFIG, PLUGIN_CONF)

    def healthCheck(self):
        return ""

    def metrics(self):
        metrics = self.plugin.getMetrics()
        return metrics

    def metricPayloadOptions(self):
        return self.plugin.loadMetricPayloadOptions(request.get_json())

    def query(self):
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
            
grappa = Grappa(CONFIG, PLUGIN_CONF, getPluginPath())

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