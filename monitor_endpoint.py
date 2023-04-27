import time

class QueryInfo:
    def __init__(self) -> None:
        self.time = round(time.time() * 1000)
        self.processingTime = -1

    def endProcessing(self):
        self.processingTime = round(time.time() * 1000) - self.time


class Monitoring:
    def __init__(self, outputFormat: str, cleanInterval: int) -> None:
        self.outputFormat = outputFormat
        self.queries = []
        self.cleanInterval = cleanInterval

    def addQuery(self, query):
        self.queries.append(query)
        self.cleanupQueries()
    
    def cleanupQueries(self):
        for i in range(len(self.queries)):
            if self.queries[i].time < (round(time.time()*1000) - self.cleanInterval):
                self.queries.pop(i)

    def getQueryCount(self):
        self.cleanupQueries()
        return len(self.queries)
    
    def getAvgProcessingTime(self):
        self.cleanupQueries()
        if len(self.queries) == 0:
            return 0
        avg = 0
        for query in self.queries:
            avg += query.processingTime
        return avg/len(self.queries)
    
    def getMinProcessingTime(self):
        self.cleanupQueries()
        if len(self.queries) == 0:
            return 0
        min = self.queries[0].processingTime
        for query in self.queries:
            if query.processingTime < min:
                min = query.processingTime
        return min
    
    def getMaxProcessingTime(self):
        self.cleanupQueries()
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
        return MonitoringOutput(self).buildResponse()

class MonitoringOutput:
    def __init__(self, monitoring: Monitoring) -> None:
        self.monitoring = monitoring
    
    def buildResponse(self):
        self.template = {
            "QueryCount": self.monitoring.getQueryCount(),
            "AverageProcessingTime": self.monitoring.getAvgProcessingTime(),
            "MinProcessingTime": self.monitoring.getMinProcessingTime(),
            "MaxProcessingTime": self.monitoring.getMaxProcessingTime(),
            "p80": self.monitoring.getPercentile(80),
            "p95": self.monitoring.getPercentile(95)
        }
        if self.monitoring.outputFormat.lower() == "json":
            return self.template
        else:
            return ""