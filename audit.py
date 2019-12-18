import csv
import glob
import itertools
import base64
import os
import json
import etcd_client
from datetime import datetime


def decode(csvs):
    # decode csvs
    for key, value in csvs.items():
        auditor = key.split('/')[3]
        payload = json.loads(value)
        encoded = payload['payload'][2:-1].encode('latin1')
        decoded = base64.b64decode(encoded)
        with open(audit_dir + '/' + auditor + '.csv', 'wb') as output:
            output.write(decoded)

def compare(list1, list2):
    diff = 0
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            diff += 1
    return diff


def compare_csv_list(filenames):
    input1 = []
    input2 = []
    output = {}
    for item in filenames:
        output[item] = 0
    for pair in itertools.permutations(filenames, 2):
        print("Comparing {} and {}".format(pair[0], pair[1]))
        with open(pair[0], 'r') as fil:
            reader1 = csv.reader(fil)
            for row in reader1:
                input1.append(row)
        with open(pair[1], 'r') as fil:
            reader1 = csv.reader(fil)
            for row in reader1:
                input2.append(row)
        output[pair[0]] += compare(input1, input2)
        input1 = []
        input2 = []
    return output


def submit(tool, audit_id, issuer):
    # find most recent csv
    path = config['DATA_REPOS'][tool]
    filenames = glob.glob("{}/*.csv".format(path))
    filenames.sort()
    # filenames[-1] is the latest file
    # if they are named appropriately
    with open(filenames[-1], 'rb') as f:
        encoded = base64.b64encode(f.read())
    # write entry with encoded payload
    etcd_client.write("csv/{}/{}".format(audit_id, issuer), '{{"tool":"{}",\
    "timestamp":"{}",\
    "payload":"{}"}}'.format(tool, datetime.now(), encoded))
    return filenames[-1]


def cleanup():
    with open('known_audits.json', 'r') as archive:
        known_audits = json.load(archive)
        print(known_audits)
    keys_to_delete = []
    for key in known_audits:
        audit_time = datetime.strptime(known_audits[key], "%Y-%m-%d %H:%M:%S.%f")
        print(audit_time)
        delta = datetime.now() - audit_time
        print(delta)
        if (delta.total_seconds() // 60) % 60 > 10:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        print("Deleting ", key)
        del known_audits[key]
    with open('known_audits.json', 'w') as archive:
        json.dump(known_audits, archive)
    return known_audits


def audit(path):
    print("Finding candidates in directory")
    filenames = glob.glob("{}/*.csv".format(path))
    print("Candidates: ", filenames)
    # Compare candidates to each other and sum the different lines
    print("For each candidate sum the number of different lines with each other candidate")
    output = compare_csv_list(filenames)
    print("Difference index per candidate: ", output)
    # Find the candidates with the minimum sum
    print("If there is a draw, the candidates with the minimum sum proceed to second round")

    best_nodes = [key for key in output if output[key] == min(output.values())]
    if len(best_nodes) > 1:
        print("Candidates in second round: ", best_nodes)
        print("If the recond round candidates are identical we can accept them")
        # If all the best candidates are identical we can automatically accept them as valid
        if max(compare_csv_list(best_nodes).values()) == 0:
            print("Best candidates are identical, elected leaders: ", best_nodes)
        else:
            # Else we cannot know if they are valid
            print("Best candidates are not identical, manual decision required")
    else:
        print("Leader elected as: ", best_nodes)
    for index in range(len(best_nodes)):
        best_nodes[index] = best_nodes[index].split('/')[-1][0:-4]
    return(best_nodes)

def validate(details, audit_id):
    #make temp folder IF not exists
    audit_dir = config['WORKING_ENVIRONMENT']['auditdir'] + '/' + audit_id
    if not os.path.isdir(audit_dir):
        os.mkdir(audit_dir)
    #get csv entries for this audit
    files = etcd_client.get('csv/{}'.format(audit_id))
    csvs = {}
    # retrieve encoded csvs
    for result in files.children:
        csvs[result.key] = result.value
    # decode csvs
    decode(csvs)
    #perform validation
    winner = audit(audit_dir)
    #announce leader
    print('##########################')
    print(audit_id)
    print(details['tool'])
    print(details['timestamp'])
    print(str(winner))
    etcd_client.write("winners/{}".format(audit_id), '{{"tool":"{}",\
    "timestamp":"{}",\
    "winner":"{}"}}'.format(details['tool'], details['timestamp'], str(winner)))
    #delete audit, csvs and temp files
    etcd_client.delete_recursive("/csv/{}".format(audit_id))
    etcd_client.delete_recursive("/audit/{}".format(audit_id))
