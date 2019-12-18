import csv
import glob
import sys
import etcd_client
import datetime


def detect(path, name):
    result = {}
    print("Data path:")
    print(path)
    result['datapath'] = path
    filenames = glob.glob("{}/control-*.csv".format(path))
    filenames.sort()
    print("Number of data snapshots: ", len(filenames))
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
        print("Current rolling average: ", avg)
        result['rolling_avg'] = avg
        print("Current value of control metric: " + control[2])
        result['control_metric'] = control[2]
        print("Absolute difference from rolling average: ", int(control[2])-avg)
        result['diff'] = int(control[2])-avg
        gain = (((int(control[2])/avg))-1)*100
        print("Gain: ", round(gain, 2), "%")
        result['gain'] = gain
        if gain > 6 or gain < -6:
            print("Data has spiked.")
            result['spike'] = True
            etcd_client.write('notifications/' + str(datetime.datetime.now()), name)
            print("Notification entry writen to cluster.")
            print(etcd_client.list('notifications'))
            return result
        else:
            print("Gain within expected margin")
            result['spike'] = False
            return result
    else:
        print("Insufficient data for running average")
        result['spike'] = False
        return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing path to control data and/or name of dataset")
    else:
        detect(sys.argv[1], sys.argv[2])
