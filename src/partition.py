import sys, argparse
import pandas as pd
import numpy as np
from itertools import repeat
from scipy.stats import entropy
from scipy.special import softmax
from scipy.sparse import csr_matrix, diags
from math import log2
from itertools import permutations

# use percentage of info gain rather than raw
pct = False

# print out data from IG calculations
verbose = False

# let nouns zero-out other nouns from adjacency matrix
zero_noun = False

# use weights in adjacency matrix, not just 1s
weighted_adj = False

# not hyperparameter, just lazy global to track whether noun has been encountered in sequence
NOUN = False

def print_progress(i, n, s):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% %d/%d (%s)" % ('='*int(20*j), 100*j, i, n, s))
    sys.stdout.flush()
    return i + 1

def load_seqs(filename):
    seqs = pd.read_csv(filename, sep=",", header=None)

    # generate permutations 'surface' for 'key'
    seqs['key'] = ""
    seqs['surface'] = ""
    for i,row in seqs.iterrows():
        try:
            key = ','.join(sorted([row[0].lower(), row[1].lower(), row[2].lower()]))
            surface = ','.join([row[0].lower(), row[1].lower(), row[2].lower()])
        except:
            key = ','.join(sorted([row[0].lower(), row[1].lower()]))
            surface = ','.join([row[0].lower(), row[1].lower()])            
        seqs.at[i, 'key'] = key
        seqs.at[i, 'surface'] = surface
    try:
        seqs = seqs.groupby(by=[0, 1, 2, 'key', 'surface']).size().reset_index(name='count')
    except:
        seqs = seqs.groupby(by=[0, 1, 'key', 'surface']).size().reset_index(name='count')
        
    return seqs[['key', 'surface', 'count']]

def load_pairs(filename):
    pairs = pd.read_csv(filename, sep=",", error_bad_lines=False, engine='python')
    pairs['awf'] = pairs['awf'].str.lower() + "/adj"
    pairs['nwf'] = pairs['nwf'].str.lower() + "/noun"
    if not weighted_adj:
        pairs['count'] = 1
    pairs.dropna(inplace=True)
    pairs = pairs.drop_duplicates()
    return pairs

def h(df, dfc):
    # get distributions
    distributions = {}
    distributions['p'] = df
    distributions['pc'] = dfc

    # get sums and entropies for each distribution
    sums = {}
    entropies = {}
    for d in distributions.keys():
        sums[d] = np.sum(distributions[d])
        if sums[d] > 0:
            entropies[d] = entropy(distributions[d], base=2)
        else:
            entropies[d] = 0

    # get proportions for each distribution
    proportions = {}
    dists = ['p']
    for d in dists:
        if (sums[d] + sums[d+'c']) > 0:
            proportions[d] = sums[d] / (sums[d] + sums[d+'c'])
        else:
            proportions[d] = 0
        proportions[d+'c'] = 1 - proportions[d]

    if verbose:
        print('distributions', distributions)
        print('sums', sums)        
        print('proportions', proportions)
        print('entropies', entropies)


    # return finish entropy
    h = proportions['p'] * entropies['p'] + proportions['pc'] * entropies['pc']

    return h


# binary entropy calculation (not currently used)
def bin_h(dist):
    ents = []
    for i in dist:
        ents.append(entropy([i, 1-i], base=2))
    return np.sum(ents)

# main partition routing (wordlist is either adjs or nouns, m is prob dist, a is adjacency matrix, a_prime is how a changes over time, w is word to partition on, and pos is w's part-of-speech)
def partition(wordlist, m, a, a_prime, w, pos):
    global NOUN

    # get prior distribution
    pre = np.squeeze(np.asarray(a_prime.sum(axis=1)))

    if pos == 'adj':

        # multiply a_prime by adj row and re-sparsify
        x = wordlist.index(w)
        a_prime = a_prime.multiply(m[x]).tocsr()

        if zero_noun and NOUN:
            # multiply a_prime again if noun rows have been zeroed-out
            ratio = np.squeeze(np.asarray(a.multiply(m[x]).sum(axis=1))) / np.squeeze(np.asarray(a.sum(axis=1)))
            a_prime = a_prime.multiply(ratio.reshape(-1,1)).tocsr()
            
    elif pos == 'noun':
        y = wordlist.index(w)

        if zero_noun:
            # use diagonal matrix multiplation to zero out rows other than y
            NOUN = True
            zeros = np.zeros(a_prime.shape[1])
            zeros[y] = 1
            D = diags(zeros)
            a_prime = a_prime * D
        else:
            # multiply a_prime by noun col and re-sparsify
            a_prime = a_prime.multiply(m[:,y].reshape(-1,1)).tocsr()

    # calculate IG
    post_y = np.squeeze(np.asarray(a_prime.sum(axis=1)*1.0))
    post_n = pre - post_y

    if np.sum(pre) > 0:
        start_ent = entropy(pre, base=2)
    else:
        start_ent = 0
    finish_ent = h(post_y, post_n)

    if not pct or start_ent == 0:
        ig = start_ent - finish_ent
    else:
        ig = (start_ent - finish_ent)/start_ent
        
    return ig, a_prime


def score(adjs, nouns, table, seqs, outfile):
    global NOUN
    outfile = open(outfile, 'w')
    outstr = "key\tsurface\ttemplate\tattest\tig_sum\tig_ent\tigs\n"
    outfile.write(outstr)
    n = len(seqs.key.unique())
    m = (table > 0) * 1
    a = csr_matrix(table).tocsr()

    print('scoring ...')
    an = 0    
    if n < 5:
        global verbose
        verbose = True

    for k,key in enumerate(seqs.key.unique()):
        if not verbose: print_progress(k+1, n, an)
        words = key.split(',')

        analyze = True
        for w in words:
            if "/adj" in w and not w in adjs:
                analyze = False
            elif "/noun" in w and not w in nouns:
                analyze = False
        if analyze:
            out = []
            for perm in list(permutations(words)):
                igs = []
                a_prime = a
                NOUN = False                
                template = ""
                for w in perm:
                    if verbose:
                        print('\n'+w)
                    if "/adj" in w and w in adjs:
                        iga, a_prime = partition(adjs, m, a, a_prime, w, 'adj')
                        igs.append(iga)
                        template += "A"
                    if "/noun" in w and w in nouns:
                        ign, a_prime = partition(nouns, m, a, a_prime, w, 'noun')
                        igs.append(ign)
                        template += "N"

                # if each word has an IG score, calculate entropy of IG scores
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
                    
                    out.append('\t'.join([key, ','.join(perm), template, str(attest), str(np.sum(igs)), str(ent), ','.join(map(str,igs))]) + "\n")

                # only write to outfile if all permutations have scores
                if len(out) == len(list(permutations(words))):
                    for line in out:
                        outfile.write(line)
                    an += 1

    outfile.close()

    
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file of adj-noun pairs [awf,nwf]')    
    parser.add_argument('-s', '--sequences', nargs=1, dest='seqs', required=True, help='comma-delimited file of sequences (no header)')
    args = parser.parse_args()

    print("processing " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])        

    print("processing " + args.seqs[0] + " ...")
    seqs = load_seqs(args.seqs[0])

    print("calculating probabilities ...")
    pairs = pairs.reindex(pairs.index.repeat(pairs['count']))
    mdf = pd.crosstab(pairs.awf, pairs.nwf)
    nouns = list(mdf.columns)
    adjs = list(mdf.index)
    table = mdf.values

    score(adjs, nouns, table, seqs, "scores.temp")
    print('')

