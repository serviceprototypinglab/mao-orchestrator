import csv
import glob
import sys
import etcd_client
import datetime
import logging


logging.basicConfig(level=logging.DEBUG)


def detect(path, name):
    result = {}
    print("Data path:")
    print(path)
    logging.debug(f"Data path: {path}")
    result['datapath'] = path
    filenames = glob.glob("{}/control-*.csv".format(path))
    filenames.sort()
    logging.debug("Number of data snapshots: {}".format(len(filenames)))
    result['snapshots'] = len(filenames)
    if len(filenames) > 2:
        control = []
        for index, filename in enumerate(filenames[-3:]):
            with open(filename, 'r') as input:
                csv_reader = csv.reader(input)
                iterrows = iter(csv_reader)
                row = next(iterrows)
                control.append(row[0])
        avg = (int(control[0]) + int(control[1]))/2
        logging.debug("Current rolling average: {}".format(avg))
        result['rolling_avg'] = avg
        logging.debug("Current value of control metric: {}".format(control[2]))
        result['control_metric'] = control[2]
        logging.debug("Absolute difference from rolling average: {}".format(int(control[2])-avg))
        result['diff'] = int(control[2])-avg
        gain = (((int(control[2])/avg))-1)*100
        logging.debug("Gain: {}%".format(round(gain, 2)))
        result['gain'] = gain
        if gain > 6 or gain < -6:
            logging.debug("Data has spiked.")
            result['spike'] = True
            etcd_client.write('notifications/' + str(datetime.datetime.now()), name)
            logging.debug("Notification entry writen to cluster.")
            logging.debug(etcd_client.list('notifications'))
            return result
        else:
            logging.debug("Gain within expected margin")
            result['spike'] = False
            return result
    else:
        logging.debug("Insufficient data for running average")
        result['spike'] = False
        return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing path to control data and/or name of dataset")
    else:
        detect(sys.argv[1], sys.argv[2])
