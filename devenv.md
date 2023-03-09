# Development Environment setup
Grafana and the backend databases will be run in docker, so a working docker installation is necessary. App is written in Python, so a >3.7 python is also required.

```
git clone ...
cd ...
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

To start the Grafana docker container with the JSON Datasource plugin installed:
```
docker run -d -p 3000:3000 --name grafana -e "GF_INSTALL_PLUGINS=simpod-json-datasource" grafana/grafana-enterprise
```

And to start the Flask proxy:
```
flask --app ./GrafanaJsonDatasourceProxy.py --debug run --host 0.0.0.0
```