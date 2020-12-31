import sys, argparse, pickle
import pandas as pd
import numpy as np
from textdistance import levenshtein
from itertools import repeat
from scipy.stats import entropy, zscore
from scipy.special import softmax
from scipy.sparse import csr_matrix, diags, hstack
from math import log2, exp
from itertools import permutations, chain, combinations
from sklearn.metrics.pairwise import cosine_similarity
from numpy.linalg import norm
from sklearn.preprocessing import binarize

# print out data from IG calculations
VERBOSE = False

# use weighted probabilities
WEIGHTED_PROBS = True

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% %d/%d" % ('='*int(20*j), np.clip(100*j, 0, 100), i, n))
    sys.stdout.flush()
    return i + 1

def load_clusters(filename):
    clusters = pd.read_csv(filename, sep=",", error_bad_lines=False, engine='python').drop_duplicates()
    return clusters

def load_nps(filename):
    nps = pd.read_csv(filename, sep="\t", error_bad_lines=False, engine='python', header=None)
    nps.columns = ['count', 'noun', 'adjs']
    nps['noun'] = nps['noun'].str.lower() + "/NOUN"
    nps['adjs'] = nps['adjs'].str.lower() + "/ADJ"
    nps.replace(',', '/ADJ,', inplace=True, regex=True)

    # recalculate count column
    #nps = nps.reindex(nps.index.repeat(nps['count']))
    #nps = nps.groupby(by=['noun', 'adjs']).size().reset_index(name='count')

    return nps

# process NPs into probabilities and expanded adjacency matrix
def process_nps(nps):
    print("processing meanings ...")    
    probs = []
    pairs = []
    features = []

    chunks = []
    vectors = []
    chunk_size = 1000

    # add adjective features
    for alist in nps.adjs.unique():
        for w in alist.split(','):
            if w not in features:
                features.append(w)

    # add noun features
    for w in nps.noun.unique():
        if w not in features:
            features.append(w)

    # create vector for each NP
    total = len(nps)

    for i,row in nps.iterrows():
        print_progress(i+1, total)
        vector = [0] * len(features)
        vector[features.index(row['noun'])] = 1
        for adj in row['adjs'].split(','):
            vector[features.index(adj)] = 1
        if WEIGHTED_PROBS:
            probs.append(np.clip(row['count'], 0, 100))
        else:
            probs.append(1)
        vectors.append(vector)

        if len(vectors) > chunk_size:
            chunks.append(csr_matrix(binarize(np.array(vectors).T)).tocsr())
            vectors = []
    chunks.append(csr_matrix(binarize(np.array(vectors).T)).tocsr())

    print("")

    print("combining vectors...")
    a_orig = hstack(chunks).tocsr()

    print("normalizing probabilities ...")
    probs = normalize(np.array(probs))
    
    print('total feature vectors:', len(probs))

    return features, probs, a_orig    

def normalize(v):
    v = v/np.sum(v)
    #v = softmax(zscore(v))
    return v
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-n', '--nps', nargs=1, dest='nps', required=True, help='tab-delimited file of [count<TAB>noun<TAB>adj,adj,...] (no header)')    
    args = parser.parse_args()

    print("loading " + args.nps[0] + " ...")
    nps = load_nps(args.nps[0])

    features, probs, a_orig = process_nps(nps)

    pkl_file = 'ig.pkl'
    print("save to " + pkl_file)
    f = open(pkl_file, 'wb')
    pickle.dump(features, f)
    pickle.dump(a_orig, f)
    pickle.dump(probs, f)    

    print('done')

