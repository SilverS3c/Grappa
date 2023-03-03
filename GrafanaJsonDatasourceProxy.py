from flask import Flask, jsonify, request
import json
import sqlite3
import sys

types = {
    "integer": "number",
    "varchar": "string",
    "timestamp": "time"
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
    return types[type]


def queryDb(request):
    # Construct table case
    response = [{"type": "table", "columns": [], "rows": []}]
    conn = sqlite3.connect("/home/zsemi02/test.db")
    for target in request["targets"]:
        response[0]["columns"] = getTableInfo(conn, target["target"])
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


    conn.close()
    return response

def queryDataFromDb(conn, request):
    cur = conn.cursor()
    obj = []
    for target in request["targets"]:
        result = cur.execute("select * from {} where time between strftime('%s', \"{}\")*1000 and strftime('%s', \"{}\")*1000;".format(target["target"], request["range"]["from"], request["range"]["to"]))    # Name of time field will be set in config
        for row in result:
            rowList = []
            for value in row:
                rowList.append(value)
            obj.append(rowList)
    return obj

def getTableInfo(conn, table):
    cursor = conn.cursor()
    cols = cursor.execute("pragma table_info({})".format(table))
    obj = []
    for col in cols:
        obj.append({"text": col[1], "type": parseType(col[2])})
    return obj


def getMetrics():
    response = []
    conn = sqlite3.connect("/home/zsemi02/test.db")
    cursor = conn.cursor()
    tables = cursor.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%';")
    for row in tables.fetchall():
        row = row[0]
        obj = {}
        obj["value"] = row
        obj["payloads"] = []

        
        cols = cursor.execute("pragma table_info({})".format(row))
        for col in cols:
            obj["payloads"].append({"name": col[1]})
        
        response.append(obj)
    conn.close()
    return response
