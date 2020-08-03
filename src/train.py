import sys, argparse, pickle
import pandas as pd
import numpy as np
from textdistance import levenshtein
from itertools import repeat
from scipy.stats import entropy, zscore
from scipy.special import softmax
from scipy.sparse import csr_matrix, diags
from math import log2, exp
from itertools import permutations, chain, combinations
from sklearn.metrics.pairwise import cosine_similarity
from numpy.linalg import norm
from sklearn.preprocessing import binarize

# print out data from IG calculations
VERBOSE = False

# use weighted probabilities
WEIGHTED_PROBS = False

# maximum number of feature vectors (can also be set with -fn argument)
MAX_VEC_NUM = 20

# maximum non-zero length of feature vectors (can also be set with -fl argument)
MAX_VEC_LEN = 2

# use full powerset of all possible features, not just attested ones
POWERSET = False

# probability normalization
NORMALIZATION = 'sum'

# cluster adjectives
CLUST_ADJ = False

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% %d/%d" % ('='*int(20*j), np.clip(100*j, 0, 100), i, n))
    sys.stdout.flush()
    return i + 1

def load_clusters(filename):
    clusters = pd.read_csv(filename, sep=",", error_bad_lines=False, engine='python').drop_duplicates()
    return clusters

def load_nps(filename, clusters, cl, clust_adj):
    nps = pd.read_csv(filename, sep="\t", error_bad_lines=False, engine='python', header=None)
    nps.columns = ['count', 'noun', 'adjs']
    nps['noun'] = nps['noun'].str.lower()
    nps['adjs'] = nps['adjs'].str.lower()

    # change nouns to their clusters
    if len(clusters) > 0:
        print('converting nouns to clusters ...')
        nps = pd.merge(nps, clusters, how='inner', left_on=['noun'], right_on=['wf'])
        del nps['noun']
        del nps['wf']        
        nps = nps.rename(columns={"cl": "noun"})
        nps = nps.astype({'noun': 'str'})

        # change adjectives to their clusters
        if clust_adj:
            print('converting adjs to clusters ...')            
            total = len(nps)
            for i,row in nps.iterrows():
                print_progress(i+1, total)
                astring = ""
                try:
                    for w in row['adjs'].split(','):
                        try:
                            acl = cl[w]
                            if len(astring) > 0:
                                astring += ","
                            astring += str(acl)
                        except:
                            pass
                except:
                    pass

                nps.at[i, 'adjs'] = astring

            print('')
            nps = nps.loc[nps['adjs'] != ""]

    # recalculate count column (probably a more efficient way to do this, but this works)
    nps = nps.reindex(nps.index.repeat(nps['count']))
    nps = nps.groupby(by=['noun', 'adjs']).size().reset_index(name='count')

    return nps

# helper function that returns a powerset from an iterable
def get_powerset(iterable, max_vec_len):
    s = list(iterable)
    minimum = 1
    if max_vec_len > -1:
        maximum = min([len(s) + 1, max_vec_len + 1])
    else:
        maximum = len(s) + 1
    return chain.from_iterable(combinations(s, r) for r in range(minimum, maximum))

# process NPs into probabilities and expanded adjacency matrix
def process_nps(nps, max_vec_len, max_vec_num):
    print("processing attested meanings ...")    
    probs = []
    pairs = []
    adjectives = []
    nouns = []

    # build up adjacency as regular python list, not numpy, for better performance
    a = []

    # get all adjectives
    for alist in nps.adjs.unique():
        for w in alist.split(','):
            if w not in adjectives:
                adjectives.append(w)

    # iterate through nouns to expand adjacency and probs
    total = len(nps.noun.unique())
    for i,noun in enumerate(nps.noun.unique()):
        print_progress(i+1, total)
        df = nps.loc[nps['noun'] == noun]

        # calculate this noun's list of adjectives
        vector = [0] * len(adjectives)        
        if POWERSET:
            noun_adjs = adjectives
        else:
            noun_adjs = []
            for j,row in df.iterrows():
                for w in row['adjs'].split(','):
                    if w not in noun_adjs:
                        noun_adjs.append(w)

        if len(noun_adjs) > 0:
            for j,row in df.iterrows():
                vector = [0] * len(adjectives)
                for adj in row['adjs'].split(','):
                    vector[adjectives.index(adj)] = 1
                if WEIGHTED_PROBS:
                    probs.append(row['count'])
                else:
                    probs.append(1)
                a.append(vector)
                nouns.append(noun)
                if max_vec_num > -1 and j > max_vec_num:
                    break                
                
            if max_vec_num != 0:
                pset = get_powerset(noun_adjs, max_vec_len)
                j = 0
            
                for s in pset:
                    sl = ','.join(list(s))
                    if not (df['adjs']==sl).any():
                        probs.append(0)
                        vector = [0] * len(adjectives)
                        for adj in list(s):
                            vector[adjectives.index(adj)] = 1
                
                        a.append(vector)
                        nouns.append(noun)
                        j += 1
                        if max_vec_num > -1 and j > max_vec_num:
                            break

    print('')
    print('converting adjacencies to numpy ...')
    a_orig = np.array(a)

    print('calculating unattested probabilities ...')
    np_probs = np.array(probs)
    np_nouns = np.array(nouns)
    total = len(np.where(np_probs == 0)[0])

    for i,p in enumerate(np.where(np_probs == 0)[0]):
        if not VERBOSE:
            print_progress(i+1, total)
        noun = nouns[p]
        attested = a_orig[list(np.where((np_nouns == noun) & (np_probs == 1))[0]),:].T
        if attested.shape[1] > 0:

            # use euclidean distance
            vec = np.array(a_orig[p])
            probs[p] = (norm(attested-vec[:,None], axis=0, ord=2).max()/attested.shape[0])**2

            # use cosine similarity
            #vector = np.broadcast_to(np.array(a_orig[p].reshape(-1,1)), attested.shape)            
            #probs[p] = cosine_similarity(vector, attested).max()

    print('')
    print('sparsifying adjacencies ...')
    a_orig = csr_matrix(binarize(a_orig.T)).tocsr()

    print('normalizing probabilities ...')
    probs = normalize(np.array(probs))
    
    return nouns, adjectives, probs, a_orig

def normalize(v):
    if NORMALIZATION == 'softmax':
        v = softmax(v)
    elif NORMALIZATION == 'minmax':
        v = (v - np.min(v)) / (np.max(v) - np.min(v))
    elif NORMALIZATION == 'sum':
        v = v/np.sum(v)
    elif NORMALIZATION == 'max':
        v = v/np.max(v)
    elif NORMALIZATION == 'zscore':
        v = softmax(zscore(v))

    return v
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-n', '--nps', nargs=1, dest='nps', required=True, help='tab-delimited file of [noun<TAB>adj,adj,...] (no header)')    
    parser.add_argument('-c', '--clusters', nargs=1, dest='clusters', required=False, help='comma-delimited file of wordform, cluster IDs [wf,cl]')
    parser.add_argument('-fn', '--num_features', nargs=1, dest='fn', required=False, help='max number of meaning vectors per noun; -1 means unlimited; default is 20')
    parser.add_argument('-fl', '--len_features', nargs=1, dest='fl', required=False, help='max non-zero length of feature vectors; -1 means unlimited; default is 2')    
    args = parser.parse_args()

    try:
        print('loading clusters from ' + args.clusters[0] + ' ...')
        clusters = load_clusters(args.clusters[0])
    except:
        clusters = pd.DataFrame()

    cl = dict(clusters.values.tolist())        

    try:
        MAX_VEC_NUM = int(args.fn[0])
    except:
        pass

    try:
        MAX_VEC_LEN = int(args.fl[0])
    except:
        pass    
    

    print("loading " + args.nps[0] + " ...")
    nps = load_nps(args.nps[0], clusters, cl, CLUST_ADJ)        

    nouns, adjs, probs, a_orig = process_nps(nps, MAX_VEC_LEN, MAX_VEC_NUM)

    pkl_file = 'ig.pkl'
    print("save to " + pkl_file)
    f = open(pkl_file, 'wb')
    pickle.dump(nouns, f)
    pickle.dump(adjs, f)
    pickle.dump(a_orig, f)
    pickle.dump(probs, f)    
    pickle.dump(cl, f)

    print('done')

