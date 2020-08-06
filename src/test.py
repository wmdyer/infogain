import sys, argparse, pickle
import pandas as pd
import numpy as np
from scipy.stats import entropy, zscore, skew
from scipy.special import softmax
from scipy.sparse import csr_matrix, diags, hstack
from math import log2, exp
from itertools import permutations, chain, combinations
#from sklearn.metrics.pairwise import cosine_similarity
from numpy.linalg import norm
from sklearn.preprocessing import binarize

VERBOSE = False
NORMALIZATION = 'sum'
PARTITION_NOUN = False

CRED = '\033[91m'
CEND = '\033[0m'


def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% %d/%d" % ('='*int(20*j), np.clip(100*j, 0, 100), i, n))
    sys.stdout.flush()
    return i + 1

def normalize(v):
    if NORMALIZATION == 'softmax':
        v = softmax(v)
    elif NORMALIZATION == 'minmax':
        v = (v - np.min(v)) / (np.max(v) - np.min(v))
    elif NORMALIZATION == 'sum':
        v = v/np.sum(v)
    elif NORMALIZATION == 'zscore':
        v = softmax(zscore(v))
    return v

def load_seqs(filename, cl, clust_adj):
    seqs = pd.read_csv(filename, sep=",", header=None)

    # generate permutations 'surface' for 'key'
    seqs['key'] = ""
    seqs['surface'] = ""
    
    for i,row in seqs.iterrows():
        w0 = row[0].lower() 
        w1 = row[1].lower()        
        try:
            w2 = row[2].lower()
        except:
            w2 = None

        try:
            if clust_adj or "/noun" in w0:
                w0 = str(cl[w0.split('/')[0]]) + "/" + w0.split('/')[1]
            if clust_adj or "/noun" in w1:                
                w1 = str(cl[w1.split('/')[0]]) + "/" + w1.split('/')[1]
            if clust_adj or "/noun" in w2:                
                w2 = str(cl[w2.split('/')[0]]) + "/" + w2.split('/')[1]
        except:
            pass

        if w2 != None:
            key = ','.join(sorted([w0, w1, w2]))
            surface = ','.join([w0, w1, w2])
        else:
            key = ','.join(sorted([w0, w1]))
            surface = ','.join([w0, w1])            
        seqs.at[i, 'key'] = key
        seqs.at[i, 'surface'] = surface
    try:
        # handle triples
        seqs = seqs.groupby(by=[0, 1, 2, 'key', 'surface']).size().reset_index(name='count')
    except:
        # handle pairs
        seqs = seqs.groupby(by=[0, 1, 'key', 'surface']).size().reset_index(name='count')

    return seqs[['key', 'surface', 'count']]

# main partition routine (wordlist is either adjs or nouns, m is prob dist, a is adjacency matrix, a_prime is how a changes over time, w is word to partition on, and pos is w's part-of-speech)
def partition(wordlist, a, probs, w, pos):
    ig = 0

    ap = {}
    if pos == 'adj':
        # multiply a by adj row and re-sparsify
        x = wordlist.index(w)
        ap['yes'] = a.multiply(binarize(a[x])).tocsr()
            
    elif pos == 'noun':

        if PARTITION_NOUN:
            # multiply a by noun col and re-sparsify
            vec = np.zeros(a.shape[1])        
            y = [i for i, x in enumerate(wordlist) if x == w]
            np.put(vec, y, 1)
            ap['yes'] = a * diags(vec)

        else:
            # get all adjs associated to noun
            y = [a[:,i] for i, x in enumerate(wordlist) if x == w]

            # multiply a by all noun adjs
            ap['yes'] = a.multiply(binarize(np.sum(hstack(y), axis=1)))


    # a_no is whatever's left of 'a' after removing a_yes
    ap['no'] = a - ap['yes']

    # sum a's columns and binarize
    qk = binarize(a.sum(axis=0))[0]
    pk = {}    
    pk['no'] = binarize(ap['no'].sum(axis=0))[0]

    # pk['yes'] is whatever's left of qk after removing pk['no']
    pk['yes'] = qk - pk['no']

    ap['yes'] = ap['yes'].multiply(pk['yes'].reshape(-1,1).T).tocsr()

    # for qk and both pk's, multiply by static probs vector, then normalize
    qk = qk*probs


    if np.sum(qk) > 0:
        qk_num = len(np.where(qk != 0)[0])
        if VERBOSE:
            print(CRED + 'qk ' + str(qk_num) + CEND, '\n', a.A, '\n', qk)    
        
        qk = normalize(qk)
        for d in ['yes', 'no']:
            pk[d] = pk[d] * probs
            if np.sum(pk[d]) > 0:
                pk_num = len(np.where(pk[d] != 0)[0])                
                pk[d] = normalize(pk[d])
                # ig is the proportion of pk[d]'s non-zero vectors to qk's non-zero vectors, times the D_KL of pk[d] from qk
                ig += (pk_num/qk_num) * entropy(pk=pk[d], qk=qk, base=2)
    
                if VERBOSE:
                    print(CRED + 'pk[' + d + '] ' + str(pk_num) + CEND, '\n', ap[d].A, '\n', pk[d])

    if VERBOSE:
        print(ig)

    return ig, ap['yes']

def score(nouns, adjs, a_orig, probs, seqs, cl, outfile):
    outfile = open(outfile, 'w')
    outstr = "key\tsurface\ttemplate\tattest\tig_sum\tig_ent\tig_var\tig_skew\tigs\n"
    outfile.write(outstr)
    n = len(seqs.key.unique())
    
    print('scoring sequences ...')
    an = 0    
    if n < 5:
        global VERBOSE
        VERBOSE = True

        if len(nouns) < 20:
            print(adjs)
            print(nouns)

    for k,key in enumerate(seqs.key.unique()):
        if not VERBOSE: print_progress(k+1, n)
        words = key.split(',')

        analyze = True

        # if words or clusters don't exist in training set, don't analyze
        for w in words:
            wf = w.split('/')[0]
            try:
                if clust_adj or "/noun" in w:
                    wf = str(cl[wf])
            except:
                pass

            if "/adj" in w and wf not in adjs:
                analyze = False
            elif "/noun" in w and wf not in nouns:
                analyze = False

        if analyze:
            out = []
            for perm in list(permutations(words)):
                igs = []
                a = a_orig
                template = ""
                if VERBOSE:
                    print("\n\n*** " + str(perm) + " ***")
                for w in perm:
                    wf = w.split('/')[0]
                    try:
                        if clust_adj or "/noun" in w:
                            wf = str(cl[wf])
                    except:
                        pass
                            
                    if VERBOSE:
                        print('\n'+w)
                    if "/adj" in w and wf in adjs:
                        iga, a = partition(adjs, a, probs, wf, 'adj')
                        igs.append(iga)
                        template += "A"
                    if "/noun" in w and wf in nouns:
                        ign, a = partition(nouns, a, probs, wf, 'noun')
                        igs.append(ign)
                        template += "N"

                # if each word has an IG score, calculate entropy and variance of IG scores and append to out string
                if len(igs) == len(words):
                    surface = ','.join(perm)                
                    try:
                        attest = seqs.loc[seqs['surface'] == surface]['count'].values[0]
                    except:
                        attest = 0

                    if template == "NA":
                        template = "AN"

                    if np.sum(igs) > 0:
                        ent = entropy(igs, base=2)
                    else:
                        ent = 0

                    var = np.var(igs)
                    sk = skew(igs)
                    
                    out.append('\t'.join([key, ','.join(perm), template, str(attest), str(np.sum(igs)), str(ent), str(var), str(sk), ','.join(map(str,igs))]) + "\n")

                # only write to outfile if all permutations have scores
                if len(out) == len(list(permutations(words))):
                    for line in out:
                        outfile.write(line)
                    an += 1

    outfile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-s', '--sequences', nargs=1, dest='seqs', required=True, help='comma-delimited file of sequences (no header), e.g., big/ADJ,red/ADJ,box/NOUN')
    args = parser.parse_args()

    pkl_file = 'ig.pkl'
    print("load from " + pkl_file)
    f = open(pkl_file, 'rb')
    nouns = pickle.load(f)
    adjs = pickle.load(f)
    a_orig = pickle.load(f)
    probs = pickle.load(f)
    cl = pickle.load(f)
    clust_adj = pickle.load(f)

    print("loading " + args.seqs[0] + " ...")
    seqs = load_seqs(args.seqs[0], cl, clust_adj)

    score(nouns, adjs, a_orig, probs, seqs, cl, "scores.tsv")
    print('')

