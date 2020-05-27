import argparse, sys
import pandas as pd
import numpy as np

#from sklearn.metrics import log_loss
from scipy.special import softmax
#from scipy.stats import entropy
from math import log2
from itertools import repeat

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_scores(filename):
    scores = pd.read_csv(filename, sep="\t", error_bad_lines=False, engine='python')
    scores['surface'] = scores['surface'].str.lower()
    return scores

def cross_entropy(targets, predictions):
    N = predictions.shape[0]
    ce = -np.sum(targets * np.log(predictions)) / N
    return ce

def cross_entropy2(p, q):
    #print(p[0]*log2(p[0]))
    return -sum([p[i]*log2(q[i]) for i in range(len(p))])
#    s=0
#    for i in range(len(p)):
#        if q[i] > 0:
#            s+=p[i]*log2(q[i])
#    return -s

def analyze(scores, domask):

    accuracies = []
    losses = []
    losses_baseline = []

    predictor = 'ig'

    total = len(scores['key'].unique())
    for i,key in enumerate(scores['key'].unique()):
        print_progress(i+1, total)
        df = scores.loc[scores['key'] == key][['surface', 'mask', 'attest', predictor]]

        dist = pd.pivot_table(df[['surface', 'mask', 'attest', predictor]], index=['surface'], values=['mask', 'attest', 'surface', predictor], aggfunc=np.sum)

        attested = np.array(dist['attest'].values)
        predicted = 1-np.array(dist[predictor].values)
        noskill = np.ones(len(attested))

        if domask:
            mask = dist['mask'].values
            mask = [float(i)/sum(mask) for i in mask]
            if i==0:
                mdf = pd.DataFrame(df[['surface', 'mask']])
            #mask = softmax(mask)
            
            loss = cross_entropy(softmax(attested*mask), softmax(predicted*mask))
            loss_baseline = cross_entropy(softmax(attested*mask), softmax(noskill*mask))
        else:
            loss = cross_entropy(softmax(attested), softmax(predicted))
            loss_baseline = cross_entropy(softmax(attested), softmax(noskill))

        if loss < loss_baseline:
            accuracies.append(1)
        else:
            accuracies.append(0)

        losses.append(loss)
        losses_baseline.append(loss_baseline)

    print('')

    if domask:
        order = {}
        mask = mdf['mask'].values
        mask = [float(i)/sum(mask) for i in mask]        
        for i,row in mdf.iterrows():
            o = row['surface'].split(',')[0].split('/')[1].replace('adj', 'A').replace('noun', 'N')
            o += row['surface'].split(',')[1].split('/')[1].replace('adj', 'A').replace('noun', 'N')
            o += row['surface'].split(',')[2].split('/')[1].replace('adj', 'A').replace('noun', 'N')            
            try:
                order[o] += mask[i]
            except:
                order[o] = mask[i]

        print('\nmask', order)

    print('\n  number of triples', len(losses))
    print(' pct above baseline', np.average(accuracies))
    print('avg prediction loss', np.average(losses))
    print('  avg baseline loss', np.average(losses_baseline))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='evaluate scores')
    parser.add_argument('-f', '--scores', nargs=1, dest='f', required=True, help='tab-delimited scores file')
    parser.add_argument('--mask', dest='mask', default=False, action='store_true', required=False, help='mask results on lang tendency')    
    args = parser.parse_args()

    scores = load_scores(args.f[0])
    analyze(scores, args.mask)
