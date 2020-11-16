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
NORMALIZATION = 'sum'
PARTITION_NOUN = True
INCLUDE_NOUN_IG = True

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
    return v

def load_seqs(filename, cl, clust_adj):
    seqs = pd.read_csv(filename, sep=",", header=None)

    seqs['key'] = ""
    #seqs['clusters'] = ""
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

# main partition routine (wordlist is either adjs or nouns, m is prob dist, a is adjacency matrix, a_prime is how a changes over time, w is word to partition on, and pos is w's part-of-speech)
def partition(wordlist, a, probs, w, pos, idx):
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
    if idx > 0:
        qk = binarize(a.sum(axis=0))[0]
    else:
        qk = np.ones(len(probs))

    pk = {}    
    pk['no'] = binarize(ap['no'].sum(axis=0))[0]

    # pk['yes'] is whatever's left of qk after removing pk['no']
    pk['yes'] = qk - pk['no']

    ap['yes'] = ap['yes'].multiply(pk['yes'].reshape(-1,1).T).tocsr()

    # for qk and both pk's, multiply by static probs vector, then normalize
    if idx > 0:
        qk = qk*probs
    else:
        qk = probs

    ig_c = {}
    ig_uc = {}
    ig_c['yes'] = 0.0
    ig_uc['yes'] = 0.0
    ig_c['no'] = 0.0
    ig_uc['no'] = 0.0   

    if idx == 0 or np.sum(qk) > 0:
        if idx > 0:
            qk_num = len(np.where(qk != 0)[0])
        else:
            qk_num = len(qk)
        if VERBOSE:
            print(CRED + 'qk ' + str(qk_num) + CEND, '\n', a.A, '\n', qk)    

        qk = normalize(qk)
        
        for d in ['yes', 'no']:
            pk[d] = pk[d] * probs
            if np.sum(pk[d]) > 0:
                pkd_nz = np.where(pk[d] != 0)[0]
                pk_num = len(pkd_nz)                
                pk[d] = normalize(pk[d])
                # ig is the proportion of pk[d]'s non-zero vectors to qk's non-zero vectors, times the D_KL of pk[d] from qk
                #ik = list(set(list(np.where(qk!=0)[0]) + list(pkd_nz)))
                if idx > 0:
                    qk_nz = np.where(qk != 0)[0]                
                    ig_uc[d] = entropy(pk=pk[d][qk_nz], qk=qk[qk_nz], base=2)
                else:
                    ig_uc[d] = entropy(pk=pk[d], qk=qk, base=2)
                ig_c[d] = (pk_num/qk_num) * ig_uc[d]
                ig += ig_c[d]
    
                if VERBOSE:
                    print(CRED + 'pk[' + d + '] ' + str(pk_num) + CEND, '\n', ap[d].A, '\n', pk[d])

    if VERBOSE:
        print(ig)

    return ig, ap['yes'], ig_uc, ig_c

def score(nouns, adjs, a_orig, probs, seqs, cl, outfile):
    outfile = open(outfile, 'w')
    outstr = "key\tclusters\twordforms\ttemplate\tattest\tig_sum\tig_seq\tig_1st_a\tig_uc_pos\tig_c_pos\tig_uc_neg\tig_c_neg\n"
    outfile.write(outstr)
    n = len(seqs.key.unique())
    
    print('scoring sequences ...')
    an = 0    
    if n < 5:
        global VERBOSE
        VERBOSE = True
        if len(adjs) < 5:
            print(adjs)
            print(nouns)
    i=1
    keys = seqs.key.unique()
    shuffle(keys)
    for key in keys:
        if not VERBOSE: i = print_progress(i, n)
        words = key.split(',')

        analyze = True

        # if words or clusters don't exist in training set, don't analyze
        #for w in words:
            #wf = w.split('/')[0]

            #if "/ADJ" in w and wf not in adjs:
            #    analyze = False
            #elif "/NOUN" in w and wf not in nouns:
            #    analyze = False


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
                cls = []

                ig_1st = 0
                if VERBOSE:
                    print("\n\n*** " + str(perm) + " ***")
                for w in perm:
                    
                    if clust_adj or "/NOUN" in w:
                        try:
                            wf = str(cl[w.lower()])
                        except:
                            wf = w

                    cls.append(wf)

                    if VERBOSE:
                        print('\n' + w + " (" + wf + ")")
                    if "/ADJ" in w and wf in adjs:
                        iga, a, ig_uc, ig_c = partition(adjs, a, probs, wf, 'adj', len(igs))
                        igs.append(iga)
                        if 'A' not in template:
                            ig_parts['c_yes'] += ig_c['yes']
                            ig_parts['uc_yes'] += ig_uc['yes']
                            ig_parts['c_no'] += ig_c['no']
                            ig_parts['uc_no'] += ig_uc['no']
                            ig_1st = iga
                        template += "A"
                    if "/NOUN" in w and wf in nouns:
                        ign, a, ig_uc, ig_c = partition(nouns, a, probs, wf, 'noun', len(igs))
                        if INCLUDE_NOUN_IG:
                            igs.append(ign)
                            ig_parts['c_yes'] += ig_c['yes']
                            ig_parts['uc_yes'] += ig_uc['yes']
                            ig_parts['c_no'] += ig_c['no']
                            ig_parts['uc_no'] += ig_uc['no']
                        else:
                            igs.append(0)
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
                    
                    out.append('\t'.join([key, ','.join(cls), ','.join(perm), template, str(attest), str(np.sum(igs)), ','.join(map(str,igs)), str(ig_1st), str(ig_parts['uc_yes']), str(ig_parts['c_yes']), str(ig_parts['uc_no']), str(ig_parts['c_no'])]) + "\n")

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
    nouns = pickle.load(f)
    adjs = pickle.load(f)
    a_orig = pickle.load(f)
    probs = pickle.load(f)
    cl = pickle.load(f)
    clust_adj = pickle.load(f)


    cl_lc = {str(k).lower(): v for k, v in cl.items()}

    print("loading " + args.seqs[0] + " ...")
    seqs = load_seqs(args.seqs[0], cl, clust_adj)

    score(nouns, adjs, a_orig, probs, seqs, cl_lc, "scores.tsv")
    print('')

