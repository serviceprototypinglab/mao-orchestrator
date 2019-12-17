import csv
from datetime import date
import requests
import json


with open('data/control-' + str(date.today()) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([900])
with open('data/control-' + str(date(2019,9,29)) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([600])
with open('data/control-' + str(date(2019,9,28)) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([630])
json_out = {
    "key": 'iam',
    "value": 'groot'
}
with open('data/insights.json', 'w') as output:
    json.dump(json_out, output)
#response = requests.post('http://mao1:8080/write',
#                         json=json_out)
#print(response)
#response = requests.post('http://0.0.0.0:8080/write',
#                         json=json_out)
#print(response)
