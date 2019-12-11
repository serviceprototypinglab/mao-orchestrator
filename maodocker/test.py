import csv
from datetime import date


with open('data/control-' + str(date.today()) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([900])
with open('data/control-' + str(date(2019,9,29)) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([600])
with open('data/control-' + str(date(2019,9,28)) + '.csv', 'w') as output:
    csv_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([630])
