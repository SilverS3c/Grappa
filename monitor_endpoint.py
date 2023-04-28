import time

class QueryInfo:
    def __init__(self) -> None:
        self.time = round(time.time() * 1000)
        self.processingTime = -1

    def endProcessing(self):
        self.processingTime = round(time.time() * 1000) - self.time


class Monitoring:
    def __init__(self, outputFormat: str, cleanInterval: int, id: str) -> None:
        self.outputFormat = outputFormat
        self.queries = []
        self.cleanInterval = cleanInterval
        self.id = id
        self.totalQueryCount = 0

    def addQuery(self, query):
        self.queries.append(query)
        self.totalQueryCount += 1
        self.cleanupQueries()
    
    def cleanupQueries(self):
        remove = []
        for i in self.queries:
            if i.time < (round(time.time()*1000) - self.cleanInterval):
                remove.append(i)
        for query in remove:
            self.queries.remove(query)

    def getQueryCount(self):
        return len(self.queries)
    
    def getAvgProcessingTime(self):
        if len(self.queries) == 0:
            return 0
        avg = 0
        for query in self.queries:
            avg += query.processingTime
        return avg/len(self.queries)
    
    def getMinProcessingTime(self):
        if len(self.queries) == 0:
            return 0
        min = self.queries[0].processingTime
        for query in self.queries:
            if query.processingTime < min:
                min = query.processingTime
        return min
    
    def getMaxProcessingTime(self):
        if len(self.queries) == 0:
            return 0
        max = self.queries[0].processingTime
        for query in self.queries:
            if query.processingTime > max:
                max = query.processingTime
        return max


    # p80 / p95: Sort the queries list by processingtime, select the (p / 100) * n   th element

    def getPercentile(self, percentile: float):
        self.cleanupQueries()
        if len(self.queries) == 0:
            return 0
        self.queries.sort(key=lambda x: x.processingTime)
        i = round((float(percentile/100) if percentile > 1 else percentile) * len(self.queries))
        return self.queries[i-1].processingTime

    def getOutput(self):
        self.cleanupQueries()
        return MonitoringOutput(self).buildResponse()

class MonitoringOutput:
    def __init__(self, monitoring: Monitoring) -> None:
        self.monitoring = monitoring

    def writePrometheusFormat(self, template: dict):
        resp = ""
        for key in template:
            resp += f"{key}" + '{id="' + self.monitoring.id + '"}' + f" {template[key]}\n"
        return resp
    
    def buildResponse(self):
        template = {
            "query_count": self.monitoring.getQueryCount(),
            "average_processing_time": self.monitoring.getAvgProcessingTime(),
            "min_processing_time": self.monitoring.getMinProcessingTime(),
            "max_processing_time": self.monitoring.getMaxProcessingTime(),
            "total_query_count": self.monitoring.totalQueryCount,
            "p80": self.monitoring.getPercentile(80),
            "p95": self.monitoring.getPercentile(95)
        }
        if self.monitoring.outputFormat.lower() == "json":
            return {f"{self.monitoring.id}": template}
        else:
            return self.writePrometheusFormat(template)