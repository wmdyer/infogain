import sys, argparse, pickle, random
import pandas as pd
import numpy as np
from scipy.stats import entropy, zscore, skew
from scipy.special import softmax
from scipy.sparse import csr_matrix, diags, hstack
from math import log2, exp
from random import shuffle
from itertools import permutations, chain, combinations
#from sklearn.metrics.pairwise import cosine_similarity
from numpy.linalg import norm
from sklearn.preprocessing import binarize

VERBOSE = False
ABLATE = True

CRED = '\033[91m'
CEND = '\033[0m'


def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% %d/%d" % ('='*int(20*j), np.clip(100*j, 0, 100), i, n))
    sys.stdout.flush()
    return i + 1

def normalize(v):
    v = v/np.sum(v)
    #v = softmax(zscore(v))
    return v

def load_seqs(filename):
    seqs = pd.read_csv(filename, sep=",", header=None)

    seqs['key'] = ""
    seqs['wordforms'] = ""    
    
    for i,row in seqs.iterrows():
        w0 = str(row[0])
        w1 = str(row[1])

        try:
            w2 = str(row[2])
        except:
            w2 = None

                    
        if w2 != None:
            key = ','.join(sorted([str(row[0]), str(row[1]), str(row[2])]))
            wordforms = ','.join([str(row[0]), str(row[1]), str(row[2])])
        else:
            key = ','.join(sorted([str(row[0]), str(row[1])]))
            wordforms = ','.join([str(row[0]), str(row[1])])
        seqs.at[i, 'key'] = key
        seqs.at[i, 'wordforms'] = wordforms        
    try:
        # handle triples
        seqs = seqs.groupby(by=[0, 1, 2, 'key', 'wordforms']).size().reset_index(name='count')
    except:
        # handle pairs
        seqs = seqs.groupby(by=[0, 1, 'key', 'wordforms']).size().reset_index(name='count')

    return seqs[['key', 'wordforms', 'count']]

# main partition routine
def partition(features, a, probs, w):
    ig = 0
    ap = {}

    # multiply a by row and re-sparsify
    x = features.index(w)
    ap['yes'] = a.multiply(binarize(a[x])).tocsr()
            
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

    ig_c = {}
    ig_uc = {}
    ig_c['yes'] = 0.0
    ig_uc['yes'] = 0.0
    ig_c['no'] = 0.0
    ig_uc['no'] = 0.0

    if np.sum(qk) > 0:
        qk_num = len(np.where(qk != 0)[0])
        qk = normalize(qk)
        
        if VERBOSE:
            print(CRED + 'qk ' + str(qk_num) + CEND, '\n', a.A, '\n', qk)    
        
        for d in ['yes', 'no']:
            pk[d] = pk[d] * probs
            if np.sum(pk[d]) > 0:
                pkd_nz = np.where(pk[d] != 0)[0]
                pk_num = len(pkd_nz)                
                pk[d] = normalize(pk[d])
                qk_nz = np.where(qk != 0)[0]                
                ig_uc[d] = entropy(pk=pk[d][qk_nz], qk=qk[qk_nz], base=2)
                ig_c[d] = (pk_num/qk_num) * ig_uc[d]
                ig += ig_c[d]
    
                if VERBOSE:
                    print(CRED + 'pk[' + d + '] ' + str(pk_num) + CEND, '\n', ap[d].A, '\n', pk[d])

    if VERBOSE:
        print(ig)

    return ig, ap['yes'], ig_uc, ig_c

def score(features, a_orig, probs, seqs, outfile):
    outfile = open(outfile, 'w')
    if ABLATE:
        outstr = "key\twordforms\ttemplate\tattest\tig_seq\tig_1st_a\tig_sum\tig_uc_pos\tig_c_pos\tig_uc_neg\tig_c_neg\n"
    else:
        outstr = "key\twordforms\ttemplate\tattest\tig_seq\tig_1st_a\n"        
    outfile.write(outstr)
    n = len(seqs.key.unique())
    
    print('scoring sequences ...')
    an = 0    
    if n < 5:
        global VERBOSE
        VERBOSE = True

    i=1
    keys = seqs.key.unique()
    shuffle(keys)
    for key in keys:
        if not VERBOSE: i = print_progress(i, n)
        words = key.split(',')

        analyze = True

        if analyze:
            out = []
            perms = list(permutations(words))

            for perm in perms:
                igs = []
                ig_parts = {}
                ig_parts['c_yes'] = 0
                ig_parts['uc_yes'] = 0
                ig_parts['c_no'] = 0
                ig_parts['uc_no'] = 0
                a = a_orig
                template = ""

                ig_1st = 0
                if VERBOSE:
                    print("\n\n*** " + str(perm) + " ***")
                for w in perm:
                    
                    if VERBOSE:
                        print('\n' + w)
                        
                    if w in features:
                        ig, a, ig_uc, ig_c = partition(features, a, probs, w)
                        ig_parts['c_yes'] += ig_c['yes']
                        ig_parts['uc_yes'] += ig_uc['yes']
                        ig_parts['c_no'] += ig_c['no']
                        ig_parts['uc_no'] += ig_uc['no']
                        
                        if "/ADJ" in w:
                            igs.append(ig)
                            if 'A' not in template:
                                ig_1st = ig
                            template += "A"
                        elif "/NOUN" in w:
                            igs.append(ig)
                            template += "N"

                # if each word has an IG score, sum IG scores and append to out string
                if len(igs) == len(words):
                    surface = ','.join(perm)                
                    try:
                        attest = seqs.loc[seqs['wordforms'] == surface]['count'].values[0]
                    except:
                        attest = 0

                    if template == "NA":
                        template = "AN"
                    if ABLATE:
                        out.append('\t'.join([key, ','.join(perm), template, str(attest), ','.join(map(str,igs)), str(ig_1st), str(np.sum(igs)), str(ig_parts['uc_yes']), str(ig_parts['c_yes']), str(ig_parts['uc_no']), str(ig_parts['c_no'])]) + "\n")
                    else:
                        out.append('\t'.join([key, ','.join(perm), template, str(attest), ','.join(map(str,igs)), str(ig_1st)]) + "\n")

                # only write to outfile if all permutations have scores
                if len(out) == len(perms):
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
    features = pickle.load(f)
    a_orig = pickle.load(f)
    probs = pickle.load(f)

    print("loading " + args.seqs[0] + " ...")
    seqs = load_seqs(args.seqs[0])

    score(features, a_orig, probs, seqs, "scores.tsv")
    print('')

