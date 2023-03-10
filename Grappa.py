from flask import Flask, jsonify, request
import json
import sqlite3
from sqlalchemy import create_engine, text, MetaData, Table, sql, exc, select
from sqlalchemy.inspection import inspect
import sys
import argparse
import logging

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
    engine = create_engine(PLUGIN_CONF["connection"]["address"])
    with engine.connect() as conn:
        metrics = getMetrics(conn)
        return metrics

@app.route('/metric-payload-options', methods = ['POST'])
def metricPayloadOptions():
    engine = create_engine(PLUGIN_CONF["connection"]["address"])
    
    with engine.connect() as conn:
        return loadMetricPayloadOptions(request.get_json(), conn)

@app.route('/query', methods = ['POST'])
def query():
    result = queryDb(request.get_json())
    return result


def parseType(type):
    return types[str(type)]


def queryDb(request):
    
    
    response = []
    targetnum = 0
    engine = create_engine(PLUGIN_CONF["connection"]["address"])
    
    with engine.connect() as conn:
        for target in request["targets"]:
            response.append({})
            if getTable(target["target"])["type"] == "table":
                # table case
                response[targetnum] = {"type": "table", "columns": [], "rows": []}
                response[targetnum]["columns"] = getTableInfo(target["target"])
                response[targetnum]["rows"] = queryDataFromDb(conn, target, request)
            else:
                # timeseries case
                timeseriesTarget = {}
                timeseriesTarget["target"] = target["target"]
                timeseriesTarget["datapoints"] = queryDataFromDb(conn, target, request)
                response[targetnum] = timeseriesTarget
            targetnum += 1
    return response

def addToStatement(stmt, payload, elem):
    if elem.startswith(">") or elem.startswith("<") or elem.startswith("!"):
        if elem[1] == "=":
            stmt = stmt.where(text("{} {} {}".format(payload, elem[:2], elem[2:])))
        else:
            stmt = stmt.where(text("{} {} {}".format(payload, elem[0], elem[1:])))
    else:
        stmt = stmt.where(text("{} = {}".format(payload, elem)))
    return stmt

def addFilteringOptions(stmt, target):
    cols = getTableColumns(target["target"])
    cols = [(col["name"]) for col in cols]
    for payload, val in target["payload"].items():
        if payload not in cols:
            continue
        if type(val) == list:
            for elem in val:
                stmt = addToStatement(stmt, payload, elem)
        else:
            stmt = addToStatement(stmt, payload, val)
    return stmt


def queryDataFromDb(conn, target, request):
    obj = []
    # Data has to be filtered based on the request payload
    if getTable(target["target"])["type"] == "timeseries":
        stmt = select(text("{},{}".format(getTableColumnNamesStr(target["target"], [getTable(target["target"])["timeColumn"]]), getTable(target["target"])["timeColumn"]))).select_from(text("{}".format(target["target"]))).where((text("{} <= strftime('%s', :to)*1000".format(getTable(target["target"])["timeColumn"])) & text("{} >= strftime('%s', :from)*1000".format(getTable(target["target"])["timeColumn"]))))
        stmt = addFilteringOptions(stmt, target)
        print(stmt)
        #result = conn.execute(text("SELECT {} FROM {} WHERE :time BETWEEN strftime('%s', :from)*1000 AND strftime('%s', :to)*1000".format(getTableColumnNamesStr(target["target"]), target["target"])), {"from": request["range"]["from"], "to": request["range"]["to"], "time": getTable(target["target"])["timeColumn"]})
        result = conn.execute(stmt, {"to": request["range"]["to"], "from": request["range"]["from"]})
    else:
        result = conn.execute(text("SELECT {} FROM {}".format(getTableColumnNamesStr(target["target"]),target["target"])))
    for row in result:
        rowList = []
        for value in row:
            rowList.append(value)
        obj.append(rowList)
    return obj

def getTableInfo(table):
    cols = getTableColumns(table)
    obj = []
    for col in cols:
        obj.append({"text": col["name"], "type": col["type"]})
    return obj


def getMetrics(conn):
    
    response = []
    tables = getTableNames()
    for row in tables:
        obj = {}
        obj["value"] = row
        obj["payloads"] = []

        
        cols = getTableColumns(row)
        for col in cols:
            payload = {"name": col["name"], "type": col["input"]}
            #if col["input"] == "select" or col["input"] == "multi-select":
                #result = conn.execute(text("SELECT DISTINCT {} FROM {}".format(col["name"], row)))
                #payload["options"] = [{"value": option[col["name"]], "label": option[col["name"]]} for option in result.mappings()]
                #payload["reloadMetric"] = True
            obj["payloads"].append(payload)

        
        response.append(obj)
    return response

def loadMetricPayloadOptions(req, conn):
    try:
        result = conn.execute(text("SELECT DISTINCT {} FROM {}".format(req["name"], req["metric"])))
        return [{"value": option[req["name"]], "label": option[req["name"]]} for option in result.mappings()]
    except exc.OperationalError:
        return []

def getTableNames():
    #insp = inspect(engine)
    #return insp.get_table_names()
    return [(table["name"]) for table in PLUGIN_CONF["database"]["tables"]]
def getTableColumns(table):
    #insp = inspect(engine)
    #return insp.get_columns(table)
    return [(col) for col in getTable(table)["columns"]]

def getTableColumnNamesStr(table, exceptions = None):
    cols = getTableColumns(table)
    tableStr = ""
    for col in cols:
        if col["name"] in exceptions:
            continue
        tableStr += col["name"] + ","
    return tableStr[:-1]

def getTable(tableName):
    for table in PLUGIN_CONF["database"]["tables"]:
        if table["name"] == tableName:
            return table

if __name__ == '__main__':
    app.run(host=CONFIG["listen"]["address"], port=CONFIG["listen"]["port"], debug=True)