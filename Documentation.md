# Grappa (Grafana Pluggable Proxy Application)

## Overview

Grappa is a Flask based Grafana JSON Datasource proxy.
It was developed for the purpose to provide a Json interface between Grafana and a freely selected backend database.
Grappa can be extended via plugins, so extra databases can be easily added. They only have to implement the functions described below.

As of now, the main application can handle 4 endpoints:
- GET /
  - Health check
- POST /metrics
  - Sending the name and type of different metrics/fields to Grafana
- POST /metric-payload-options
  - Sending the payload of the drop-down metrics to Grafana
- POST /query
  - Receiving the payload information and responding with the retrieved data

For more information about the endpoints and request response formats: https://github.com/simPod/GrafanaJsonDatasource

## Start Grappa with existing plugin

```python3 grappa.py -b/--backend <plugin> -i/--id <app identifier>  ```

With this command the Grappa will load the specified plugin and the associated config file.
The available plugins are listed by grappa if wrong, or no plugin name is supplied.

The listening port and address, logging and loadable plugins can be configured in the main config file.

Main config example:
```
{
    "log": {
        "format": "json",
        "level": "info",
        "file": "/home/user/logs/grappa.log",
        "rotation": {
            "active": "size",
            "size": "5M",
            "backupCount": 1,
            "time": 0
        }
    },
    "plugins": [
        {"name": "mysql", "file": "sql", "config": "config/plugins/mysql.json"},
        {"name": "sqlite", "file": "sql", "config": "config/plugins/sql.json"},
        {"name": "influxdb", "file": "influxdb", "config": "config/plugins/influxdb.json"}
    ],
    "listen": 
    {
        "port": 5000,
        "address": "0.0.0.0"
    }
}
```
The name of the plugin is which one supplies when starting Grappa, and the 'file' is what the application will load at startup. Every plugin has its own "plugin config", which is responsible to configure everything in connection with the plugin. It's unique for every plugin.

To build a docker image from Grappa, issue the following command in the root directory:
``` sudo docker build -t grappa . ```

To start the created image type:
``` sudo docker run -e BACKEND=<backend> -e ID=<id> -p 5000:5000 -d grappa ```
Two environment variables are necessary, BACKEND and ID.
Note: Don't forget to change the port in the Dockerfile and in the command line if it's other than the default 5000!

The config path is by default ``` ./config/main.json ```, but it can be changed via the ``` MAIN_CONFIG_PATH ``` environment variable.

## Creating new plugin

Every new plugin needs to be placed in the application's root directory, and is required to extend the PluginBase class from PluginBase.py.
The main class of the plugin needs to be called "Plugin", and has to implement the methods declared in PluginBase.
These are the following:

```
def getMetrics(self, request)

def loadMetricPayloadOptions(self, req)

def queryDb(self, request)
```

The plugin file must be included in the main config in order to work. This is done by adding a new line in the "plugins" list, in the following format:

```{"name": "<PluginName>", "file": "<PluginFile>", "config": "<PathToConfig>"}```

The getMetrics method will be called when Grafana is sending a request to the /metrics endpoint.

The loadMetricPayloadOptions is called when a request from Grafana reaches the /metric-payload-options endpint.

The queryDb method is responsible for retrieving the data from the datavase and to send it back to Grafana in the correct format.
It is being called when Grafana sends a request to /query

The format of the responses must conform with the specification defined in the Json Datasouce documentation (https://github.com/simPod/GrafanaJsonDatasource)

## Authentication

Grappa has an optional feature which can authenticate users with the HTTP Basic Auth,
and only let the authorized users to contact with the proxy.

The authentication feature can be turned on or off in the main config file.
Similarly, users can be added in the main config file, in the "users" section in the following format:

```
"users": [
        {"username": "test", "password": "688787d8ff144c502c7f5cffaafe2cc588d86079f9de88304c26b0cb99ce91c6"}
    ]
```

The password must be hashed with SHA256, and the hexdigest should be written in the "password" field.

## Monitoring

The ``` /monitor ``` endpoint is responsible for providing with various monitoring data. These are:
  - query_count
  - average_processing_time
  - min_processing_time
  - max_processing_time
  - total_query_count
  - p80
  - p95
  - unique_users

The endpoint is only available for users who can authenticate as one of the monitoring group users. The user list can be specified in the main config.

The output format can be either JSON or Prometheus compatible.

## Known issues

- In the case when in Grafana explore query builder there are more than one metrics available in the list,
a behavior is present where if a payload value is defined,
and then the query builder is being swithed to another metric from the list,
then an error message will appear saying that the payload option is not defined.
The error is present even in the official Grafan Json Datasource sample server,
so it can be assumed this is the expected behavior of the Grafana plugin,
as it doesn't unset the playload options even after changing metrics.

- The query builder's multi-select input fields can present unwanted behavior. 
Sometimes more values appear than what was defined, and sometimes the same label appears multiple times in the "selected" field,
despite the server only returning the same structure, where they only appear once.
This bug seems to appear randomly. Previously, when the multi-select options were sent out via the initial metric response,
it presented even more unwanted behavior, however since the option values are sent out exclusively via the dedicated "/metric-payload-options" endpoint,
the function seems to be working better.