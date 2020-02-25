import csv
import glob
import itertools
import base64
import os
import json
import etcd_client
import logging
import configparser
from datetime import datetime


logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')

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
        logging.debug("Comparing {} and {}".format(pair[0], pair[1]))
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
        logging.debug(known_audits)
    keys_to_delete = []
    for key in known_audits:
        audit_time = datetime.strptime(known_audits[key], "%Y-%m-%d %H:%M:%S.%f")
        logging.debug(audit_time)
        delta = datetime.now() - audit_time
        logging.debug(delta)
        if (delta.total_seconds() // 60) % 60 > 10:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        logging.debug("Deleting ", key)
        del known_audits[key]
    with open('known_audits.json', 'w') as archive:
        json.dump(known_audits, archive)
    return known_audits


def audit(path):
    logging.info("Finding candidates in directory")
    filenames = glob.glob("{}/*.csv".format(path))
    logging.info("Candidates: ", filenames)
    # Compare candidates to each other and sum the different lines
    logging.info("For each candidate sum the number of different lines with each other candidate")
    output = compare_csv_list(filenames)
    logging.info("Difference index per candidate: ", output)
    # Find the candidates with the minimum sum
    logging.info("If there is a draw, the candidates with the minimum sum proceed to second round")

    best_nodes = [key for key in output if output[key] == min(output.values())]
    if len(best_nodes) > 1:
        logging.info("Candidates in second round: ", best_nodes)
        logging.info("If the recond round candidates are identical we can accept them")
        # If all the best candidates are identical we can automatically accept them as valid
        if max(compare_csv_list(best_nodes).values()) == 0:
            logging.info("Best candidates are identical, elected leaders: {}".format(best_nodes))
        else:
            # Else we cannot know if they are valid
            logging.info("Best candidates are not identical, manual decision required")
    else:
        logging.info("Leader elected as: {}".format(best_nodes))
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
    logging.info(audit_id)
    logging.info(details['tool'])
    logging.info(details['timestamp'])
    logging.info(str(winner))
    etcd_client.write("winners/{}".format(audit_id), '{{"tool":"{}",\
    "timestamp":"{}",\
    "winner":"{}"}}'.format(details['tool'], details['timestamp'], str(winner)))
    #delete audit, csvs and temp files
    etcd_client.delete_recursive("/csv/{}".format(audit_id))
    etcd_client.delete_recursive("/audit/{}".format(audit_id))
