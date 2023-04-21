import time

class QueryInfo:
    def __init__(self) -> None:
        self.time = round(time.time() * 1000)
        self.processingTime = -1

    def endProcessing(self):
        self.processingTime = round(time.time() * 1000) - self.time

class Monitoring:
    def __init__(self, outputFormat) -> None:
        self.outputFormat = outputFormat
        self.queries = []

    def addQuery(self, query):
        self.queries.append(query)
    
    def cleanupQueries(self, interval):
        for i in range(len(self.queries)):
            if self.queries[i].time < (round(time.time()*1000) - interval):
                self.queries.pop(i)

    def getOutput(self):
        return ""