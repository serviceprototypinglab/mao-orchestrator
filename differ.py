import csv
import glob
import sys
import syncer
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
        with open(filenames[-3], 'r') as input:
            csv_reader = csv.reader(input)
            iterrows = iter(csv_reader)
            row = next(iterrows)
            control1 = row[0]
        with open(filenames[-2], 'r') as input:
            csv_reader = csv.reader(input)
            iterrows = iter(csv_reader)
            row = next(iterrows)
            control2 = row[0]
        avg = (int(control1) + int(control2))/2
        print("Current rolling average: ", avg)
        result['rolling_avg'] = avg
        with open(filenames[-1], 'r') as input:
            csv_reader = csv.reader(input)
            iterrows = iter(csv_reader)
            row = next(iterrows)
            control3 = row[0]
        print("Current value of control metric: " + control3)
        result['control_metric'] = control3
        print("Absolute difference from rolling average: ", int(control3)-avg)
        result['diff'] = int(control3)-avg
        gain = (((int(control3)/avg))-1)*100
        print("Gain: ", round(gain, 2), "%")
        result['gain'] = gain
        if gain > 20 or gain < -20:
            print("Data has spiked.")
            result['spike'] = True
            syncer.write('notifications/' + str(datetime.datetime.now()), name)
            print("Notification entry writen to cluster.")
            print(syncer.list('notifications'))
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
