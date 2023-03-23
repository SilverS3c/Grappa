import json
import sqlite3
from sqlalchemy import create_engine, text, MetaData, Table, sql, exc, select, or_
from sqlalchemy.inspection import inspect
import logging
import datetime
from flask import Response, request
from PluginBase import PluginBase


class Plugin(PluginBase):

    def queryDb(self, request):
        response = []
        targetnum = 0
        engine = create_engine(self.PLUGIN_CONF["connection"]["address"])
        
        try:
            with engine.connect() as conn:
                for target in request["targets"]:
                    response.append({})
                    if self.getTable(target["target"])["type"] == "table":
                        # table case
                        response[targetnum] = {"type": "table", "columns": [], "rows": []}
                        response[targetnum]["columns"] = self.getTableInfo(target["target"])
                        response[targetnum]["rows"] = self.queryDataFromDb(conn, target, request)
                    else:
                        # timeseries case
                        timeseriesTarget = {}
                        timeseriesTarget["target"] = target["target"]
                        timeseriesTarget["datapoints"] = self.queryDataFromDb(conn, target, request)
                        response[targetnum] = timeseriesTarget
                    targetnum += 1
        except Exception as e:
            self.logger.error(e, extra={"type": "", "method": "", "endpoint": "/query"})
            return Response(str(e), status=500)
        return response

    def addToStatementOr(self, vals, payload, elem):
        if elem.startswith(">") or elem.startswith("<"):
            if elem[1] == "=":
                vals.append(text("{} {} {}".format(payload, elem[:2], elem[2:])))
            else:
                vals.append(text("{} {} {}".format(payload, elem[0], elem[1:])))
        elif elem.startswith("!="):
            if type(elem) is int:
                vals.append(text("{} {} {}".format(payload, elem[:2], elem[2:])))
            elif type(elem) is str:
                vals.append(text("{} {} '{}'".format(payload, elem[:2], elem[2:])))
        else:
            if type(elem) is int:
                vals.append(text("{} = {}".format(payload, elem)))
            elif type(elem) is str:
                vals.append(text("{} = '{}'".format(payload, elem)))

    def addToStatement(self, stmt, payload, elem):
        if elem.startswith(">") or elem.startswith("<"):
            if elem[1] == "=":
                stmt = stmt.where(text("{} {} {}".format(payload, elem[:2], elem[2:])))
            else:
                stmt = stmt.where(text("{} {} {}".format(payload, elem[0], elem[1:])))
        elif elem.startswith("!="):
            if type(elem) is int:
                stmt = stmt.where(text("{} {} {}".format(payload, elem[:2], elem[2:])))
            elif type(elem) is str:
                stmt = stmt.where(text("{} {} '{}'".format(payload, elem[:2], elem[2:])))
        else:
            if type(elem) is int:
                stmt = stmt.where(text("{} = {}".format(payload, elem)))
            elif type(elem) is str:
                stmt = stmt.where(text("{} = '{}'".format(payload, elem)))
        return stmt

    def addFilteringOptions(self, stmt, target):
        cols = self.getTableColumns(target["target"])
        cols = [(col["name"]) for col in cols]
        for payload, val in target["payload"].items():
            if payload not in cols:
                continue
            if type(val) == list:
                vals = []
                for elem in val:
                    self.addToStatementOr(vals, payload, elem)
                stmt = stmt.where(or_(*vals))

            else:
                stmt = self.addToStatement(stmt, payload, val)
        return stmt


    def queryDataFromDb(self, conn, target, request):
        obj = []
        # Data has to be filtered based on the request payload
        if self.getTable(target["target"])["type"] == "timeseries":
            dateFrom = datetime.datetime.strptime(request["range"]["from"], '%Y-%m-%dT%H:%M:%S.%fZ')
            dateFrom = str((dateFrom - datetime.datetime(1970, 1, 1)).total_seconds()*1000)
            dateFrom = dateFrom[:-2]

            dateTo = datetime.datetime.strptime(request["range"]["to"], '%Y-%m-%dT%H:%M:%S.%fZ')
            dateTo = str((dateTo - datetime.datetime(1970, 1, 1)).total_seconds()*1000)
            dateTo = dateTo[:-2]

            stmt = select(text("{},{}".format(self.getTableColumnNamesStr(target["target"], [self.getTable(target["target"])["timeColumn"]]), self.getTable(target["target"])["timeColumn"]))).select_from(text("{}".format(target["target"]))).where((text("{} <= :to".format(self.getTable(target["target"])["timeColumn"])) & text("{} >= :from".format(self.getTable(target["target"])["timeColumn"]))))
            stmt = self.addFilteringOptions(stmt, target)
            result = conn.execute(stmt, {"to": dateTo, "from": dateFrom})
        else:
            stmt = select(text("{}".format(self.getTableColumnNamesStr(target["target"])))).select_from(text("{}".format(target["target"])))
            stmt = self.addFilteringOptions(stmt, target)
            result = conn.execute(stmt)
        for row in result:
            rowList = []
            for value in row:
                rowList.append(value)
            obj.append(rowList)
        return obj

    def getTableInfo(self, table):
        cols = self.getTableColumns(table)
        obj = []
        for col in cols:
            obj.append({"text": col["name"], "type": col["type"]})
        return obj


    def getMetrics(self):
        response = []
        tables = self.getTableNames()
        for row in tables:
            obj = {}
            obj["value"] = row
            obj["payloads"] = []

            
            cols = self.getTableColumns(row)
            for col in cols:
                payload = {"name": col["name"], "type": col["input"]}
                obj["payloads"].append(payload)

            
            response.append(obj)
        return response

    def loadMetricPayloadOptions(self, req):
        engine = create_engine(self.PLUGIN_CONF["connection"]["address"])
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT DISTINCT {} FROM {}".format(req["name"], req["metric"])))
                return [{"value": option[req["name"]], "label": option[req["name"]]} for option in result.mappings()]
            except exc.OperationalError as e:
                self.logger.info(str(e), extra={"type": "", "method": "", "endpoint": request.path})
                return []

    def getTableNames(self):
        return [(table["name"]) for table in self.PLUGIN_CONF["database"]["tables"]]
    def getTableColumns(self, table):
        return [(col) for col in self.getTable(table)["columns"]]

    def getTableColumnNamesStr(self, table, exceptions = []):
        cols = self.getTableColumns(table)
        tableStr = ""
        for col in cols:
            if col["name"] in exceptions:
                continue
            tableStr += col["name"] + ","
        return tableStr[:-1]

    def getTable(self, tableName):
        for table in self.PLUGIN_CONF["database"]["tables"]:
            if table["name"] == tableName:
                return table
        self.logger.info("No such table in config file " + tableName, extra={"type": "", "method": "", "endpoint": request.path})
        raise Exception("No such table in config file " + tableName)
    