from flask import Flask, jsonify, request
import json
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.inspection import inspect
import sys
import argparse

argparser = argparse.ArgumentParser(description="python3 grappa.py -b/--backend <plugin> -i/--id <app identifier>")


def loadMainConfig(path="./config/main.json"):
    with open(path, "r") as conf:
        return json.load(conf)
    

    
CONFIG = loadMainConfig()


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

types = {
    "integer": "number",
    "varchar": "string",
    "timestamp": "time",
    "INTEGER": "number",
    "TIMESTAMP": "time",
}

app = Flask(__name__)

@app.route("/")
def healthCheck():
    return ""

@app.route("/metrics", methods=['POST'])
def metrics():
    metrics = getMetrics()
    return metrics

@app.route('/metric-payload-options', methods = ['POST'])
def metricPayloadOptions():
    return []

@app.route('/query', methods = ['POST'])
def query():
    result = queryDb(request.get_json())
    return result


def parseType(type):
    return types[str(type)]


def queryDb(request):
    # Construct table case
    response = [{"type": "table", "columns": [], "rows": []}]
    engine = create_engine(PLUGIN_CONF["connection"]["address"])
    
    with engine.connect() as conn:
        for target in request["targets"]:
            response[0]["columns"] = getTableInfo(engine, target["target"])
        response[0]["rows"] = queryDataFromDb(conn, request)
    
    #timeseries case

    #response = []
    
    #for target in request["targets"]:
    #    timeseriesTarget = {}
    #    timeseriesTarget["target"] = target["target"]
    #    timeseriesTarget["datapoints"] = []

    #    cur = conn.cursor()

    #    result = cur.execute("select cpu, time from {} where time between strftime('%s', \"{}\")*1000 and strftime('%s', \"{}\")*1000;".format(target["target"], request["range"]["from"], request["range"]["to"]))

    #    for row in result:
    #        rowList = []
    #        for value in row:
    #            rowList.append(value)
    #        timeseriesTarget["datapoints"].append(rowList)
    #    response.append(timeseriesTarget)


    return response

def queryDataFromDb(conn, request):
    obj = []
    for target in request["targets"]:
        result = conn.execute(text("SELECT * FROM {} WHERE time BETWEEN strftime('%s', :from)*1000 AND strftime('%s', :to)*1000".format(target["target"])), {"from": request["range"]["from"], "to": request["range"]["to"]})    # Name of time field will be set in config
        for row in result:
            rowList = []
            for value in row:
                rowList.append(value)
            obj.append(rowList)
    return obj

def getTableInfo(engine, table):
    cols = getTableColumns(engine, table)
    obj = []
    for col in cols:
        obj.append({"text": col["name"], "type": parseType(col["type"])})
    return obj


def getMetrics():
    response = []
    engine = create_engine(PLUGIN_CONF["connection"]["address"])
    tables = getTableNames(engine)
    for row in tables:
        obj = {}
        obj["value"] = row
        obj["payloads"] = []

        
        cols = getTableColumns(engine, row)
        for col in cols:
            obj["payloads"].append({"name": col["name"]})
        
        response.append(obj)
    return response

def getTableNames(engine):
    insp = inspect(engine)
    return insp.get_table_names()
def getTableColumns(engine, table):
    insp = inspect(engine)
    return insp.get_columns(table)

if __name__ == '__main__':
    app.run(host=CONFIG["listen"]["address"], port=CONFIG["listen"]["port"], debug=True)