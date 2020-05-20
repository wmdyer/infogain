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
    results = []
    
    for i,row in scores.iterrows():
        prediction = row[0]
        igs = row[4:].values
        predicted_value = igs[orders.index(prediction)]
        deviation = list(np.sort(igs)).index(predicted_value)
        results.append(deviation)

    r = len(orders)
    avg = np.average(results)
    print((r-avg)/r)
