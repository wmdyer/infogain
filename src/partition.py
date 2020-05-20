import sys
import pandas as pd
import numpy as np
from scipy.stats import entropy
import argparse

def load_triples(filename):
    triples = pd.read_csv(filename, sep=",", header=None)
    return triples

def load_pairs(filename):
    pairs = pd.read_csv(filename, sep=",", error_bad_lines=False, engine='python')
    pairs['count'] = 1
    pairs.dropna(inplace=True)
    return pairs

# pairs is adj-noun pairs, a is adj1, b is adj2, counts is count of adjs, n is noun or None
def partition(pairs, a, b, counts, n):

    # define whether IG should be a pct of starting entropy
    percentage = True

    # get counts of adjs that overlap adj a
    nouns_a = pairs.loc[pairs['awf'] == a]['nwf']
    adjs_a = pairs.loc[pairs['nwf'].isin(nouns_a)]
    adjs_a = pd.pivot_table(adjs_a[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum)

    # get counts of adjs that overlap adj b
    nouns_b = pairs.loc[pairs['awf'] == b]['nwf']
    adjs_b = pairs.loc[pairs['nwf'].isin(nouns_b)]
    adjs_b = pd.pivot_table(adjs_b[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum)

    # if noun is specified, change domain to just adjs associated to noun n
    if n != None:
        adjs_n = pairs.loc[pairs['nwf'] == n]['awf']
    else:
        adjs_n = pairs.loc[(pairs['nwf'].isin(nouns_a.values)) | (pairs['nwf'].isin(nouns_b.values))]['awf'].drop_duplicates()
        #adjs_n = pairs['awf'].drop_duplicates()

    # join adjs_a, adjs_n, and counts
    adjs = pd.merge(adjs_a, adjs_n, how='right', left_on=['awf'], right_on=['awf']).fillna(0).drop_duplicates()
    dfa = pd.merge(adjs, counts, how='left', left_on=['awf'], right_index=True).fillna(0).drop_duplicates()

    # join adjs_b, adjs_n, and counts
    adjs = pd.merge(adjs_b, adjs_n, how='right', left_on=['awf'], right_on=['awf']).fillna(0).drop_duplicates()
    dfb = pd.merge(adjs, counts, how='left', left_on=['awf'], right_index=True).fillna(0).drop_duplicates()

    dfa.set_index('awf', inplace=True)
    dfb.set_index('awf', inplace=True)

    dfa['pa'] = dfa['count_x']
    dfa['pac'] = (dfa['count_y'] - dfa['count_x'])
        
    dfb['pb'] = dfb['count_x']
    dfb['pbc'] = (dfb['count_y'] - dfb['count_x'])
        
    dfa['pab'] = dfa['pa'] * (dfb['count_x']/dfb['count_y'])
    dfa['pabc'] = dfa['pa'] * ((dfb['count_y'] - dfb['count_x'])/dfb['count_y'])
        
    dfb['pba'] = dfb['pb'] * (dfa['count_x']/dfa['count_y'])
    dfb['pbac'] = dfb['pb'] * ((dfa['count_y'] - dfa['count_x'])/dfa['count_y'])
    
    # get distributions
    distributions = {}
    for d in ['pa', 'pac', 'pab', 'pabc']:
        distributions[d] = np.nan_to_num(dfa[d].values, 0)
    for d in ['pb', 'pbc', 'pba', 'pbac']:
        distributions[d] = np.nan_to_num(dfb[d].values, 0)

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
    dists = ['pa', 'pb', 'pab', 'pba']
    for d in dists:
        if (sums[d] + sums[d+'c']) > 0:
            proportions[d] = sums[d] / (sums[d] + sums[d+'c'])
        else:
            proportions[d] = 0
        proportions[d+'c'] = 1 - proportions[d]

    # calc starting entropies
    start_ents = {}
    try:
        start_ents['a'] = entropy(dfa['count_y'].values, base=2)
    except:
        start_ents['a'] = 0
    try:
        start_ents['ab'] = entropy(dfa['count_x'].values, base=2)
    except:
        start_ents['ab'] = 0
    try:
        start_ents['b'] = entropy(dfb['count_y'].values, base=2)
    except:
        start_ents['b'] = 0
    try:
        start_ents['ba'] = entropy(dfb['count_x'].values, base=2)
    except:
        start_ents['ba'] = 0

    # calc resulting entropies
    H = {}
    H['a'] = proportions['pa'] * entropies['pa'] + proportions['pac'] * entropies['pac']
    H['ab'] = proportions['pab'] * entropies['pab'] + proportions['pabc'] * entropies['pabc']
    H['b'] = proportions['pb'] * entropies['pb'] + proportions['pbc'] * entropies['pbc']
    H['ba'] = proportions['pba'] * entropies['pba'] + proportions['pbac'] * entropies['pbac']

    # calc IG (percentage reduction)
    IG = {}
    for d in ['a', 'ab', 'b', 'ba']:
        IG[d] = (start_ents[d] - H[d]) / start_ents[d]
                
    return [IG['a'], IG['ab'], IG['b'], IG['ba']]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file of adj-noun pairs [awf,nwf]')    
    parser.add_argument('-t', '--triples', nargs=1, dest='triples', required=True, help='comma-delimited file of adj-adj-noun triples (no header)')
    args = parser.parse_args()

    print("loading pairs from " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])        
    counts = pd.pivot_table(pairs[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum).dropna()  

    print("loading triples from " + args.triples[0] + " ...")
    triples = load_triples(args.triples[0])

    if 'triples' in args.triples[0]:
        outfile = args.triples[0].replace('triples', 'scores')
    else:
        outfile = "scores.csv"
        
    outfile = open(outfile, 'w')
    outfile.write("order,a,b,n,ig_abn,ig_ban,ig_anb,ig_bna,ig_nab,ig_nba\n")

    total = triples.shape[0]

    for i,row in triples.iterrows():
        if "NOUN" in row[0]:
            n = row[0]            
            a = row[1]
            b = row[2]
            order = "nab"
        elif "NOUN" in row[1]:
            a = row[0]
            n = row[1]
            b = row[2]
            order = "anb"
        else:
            a = row[0]
            b = row[1]
            n = row[2]
            order = "abn"

        # just get lowercase wordforms
        a = a.split('/')[0].lower()
        b = b.split('/')[0].lower()
        n = n.split('/')[0].lower()

        # make sure adjs aren't the same and are in pairs data
        if a != b and len(pairs.loc[pairs['awf'] == a]) > 0 and len(pairs.loc[pairs['awf'] == b]) > 0:
            igs_pre = partition(pairs, a, b, counts, None)
            igs_post = partition(pairs, a, b, counts, n)

            outputs = []

            # ig_abn
            outputs.append(igs_pre[0] + igs_pre[1])

            # ig_ban
            outputs.append(igs_pre[2] + igs_pre[3])

            # ig_anb
            outputs.append(igs_pre[0] + igs_post[2])

            # ig_bna
            outputs.append(igs_pre[2] + igs_post[0])

            # ig_nab
            outputs.append(igs_post[0] + igs_post[1])

            # ig_nba
            outputs.append(igs_post[2] + igs_post[3])

            out = ','.join([order, a, b, n] + list(map(str, outputs)))
                        
            print(str(i+1) + "/" + str(total), out)
            outfile.write(out + "\n")

    outfile.close()
    
