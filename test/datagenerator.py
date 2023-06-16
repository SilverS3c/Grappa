import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import mysql.connector
#import psutil
import time
import random
from os import getenv


bucket = getenv("BUCKET")
token = getenv("TOKEN")
influx_address = getenv("INFLUXDB_ADDRESS")
org = getenv("ORG")

mysql_address = getenv("MYSQL_ADDRESS")
mysql_username = getenv("MYSQL_USERNAME")
mysql_password = getenv("MYSQL_PASSWORD")
mysql_database = getenv("MYSQL_DATABASE")
mysql_port = getenv("MYSQL_PORT")


client = influxdb_client.InfluxDBClient(url=influx_address,
                                        token=token,
                                        org=org,
                                        )


mysqlDb = mysql.connector.connect(
    host = mysql_address,
    port=mysql_port,
    user = mysql_username,
    password = mysql_password,
    database = mysql_database
    )

write_api = client.write_api(write_options=SYNCHRONOUS)
#psutil.cpu_percent()

choices = [
        {"name": "HU",  "servers": ["Budapest"]},
        {"name": "USA", "servers": ["New York", "Chicago"]},
        {"name": "DE",  "servers": ["Berlin"]}
    ]

print("Running...")

def sendInflux():
    #cpu = psutil.cpu_percent()
    #ram = psutil.virtual_memory()[2]
    cpu = float(random.randrange(0, 60))
    ram = float(random.randrange(60, 100))
    
    choice = random.choice(choices)
    point = influxdb_client.Point("usage").tag("country", choice["name"]).tag("server", random.choice(choice["servers"])).field("cpu", cpu).field("ram", ram)
    write_api.write(bucket=bucket, org=org, record=point)

def sendMySql():
    cursor = mysqlDb.cursor()
    cpu = float(random.randrange(0, 60))
    ram = float(random.randrange(60, 100))

    sql = "INSERT INTO cpu_usage (cpu) VALUES (%s);"
    val = (cpu,)
    cursor.execute(sql, val)

    sql = "INSERT INTO ram_usage (ram) VALUES (%s);"
    val = (ram,)
    cursor.execute(sql, val)

    mysqlDb.commit()

while True:
    time.sleep(3)
    sendInflux()
    sendMySql()
    
    

