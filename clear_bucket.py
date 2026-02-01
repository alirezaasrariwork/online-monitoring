from influxdb_client import InfluxDBClient
from datetime import datetime

# InfluxDB connection info
INFLUX_URL = "http://localhost:8086"  # your InfluxDB URL
INFLUX_TOKEN = "my-token"             # your token
INFLUX_ORG = "my-org"                  # your org
INFLUX_BUCKET = "monitoring"           # bucket to clear

# Connect to InfluxDB
client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

delete_api = client.delete_api()

# Delete all data from the bucket
start = "1970-01-01T00:00:00Z"                  # beginning of epoch
stop = datetime.utcnow().isoformat() + "Z"      # current time

# predicate=None deletes everything
delete_api.delete(start=start, stop=stop, bucket=INFLUX_BUCKET, org=INFLUX_ORG, predicate=None)

print(f"✅ All data in bucket '{INFLUX_BUCKET}' has been deleted.")
