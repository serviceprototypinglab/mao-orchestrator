import csv
import glob
import itertools
import base64


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
