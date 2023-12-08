FROM python:3-slim

WORKDIR /grappa
RUN apt-get install -y build-essential python3-dev libldap2-dev libsasl2-dev slapd ldap-utils tox lcov valgrind
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY PluginBase.py .
COPY monitor_endpoint.py .
COPY influxdb.py .
COPY sql.py .
COPY Grappa.py .
COPY config/ .
CMD python ./Grappa.py -b $BACKEND -i $ID