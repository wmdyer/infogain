import sys, argparse, re
import pandas as pd
import numpy as np

def load_scores(filename):
    scores = pd.read_csv(filename, sep=",")
    return scores

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ranked accuracy')
    parser.add_argument('-f', '--file', nargs=1, dest='f', required=True, help='csv score file')
    args = parser.parse_args()

    filename = args.f[0]
    scores = load_scores(filename)

    orders = list(scores.columns[4:])
    results = {}
    for o in orders:
        results[o] = []
    
    for i,row in scores.iterrows():
        actual = row[0]
        igs = row[4:].values
        actual_value = igs[orders.index(actual)]
        deviation = list(np.sort(igs)).index(actual_value)
        results[actual].append(deviation)

    r = len(orders)
    for key in results.keys():
        if len(results[key]) > 0:
            avg = np.average(results[key])
            print(key, (r-avg)/r)
