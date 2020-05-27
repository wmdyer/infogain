import sys, argparse
import pandas as pd
import numpy as np
from itertools import repeat
from scipy.stats import entropy
from scipy.special import softmax
from math import log2

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_triples(filename):
    triples = pd.read_csv(filename, sep=",", header=None)
    triples['key'] = ""
    triples['surface'] = ""
    for i,row in triples.iterrows():
        key = ','.join(sorted([row[0].lower(), row[1].lower(), row[2].lower()]))
        surface = ','.join([row[0].lower(), row[1].lower(), row[2].lower()])
        triples.at[i, 'key'] = key
        triples.at[i, 'surface'] = surface
    print("counting attested orders ...")
    triples = triples.groupby(by=[0, 1, 2, 'key', 'surface']).size().reset_index(name='count')
    return triples

def load_pairs(filename):
    pairs = pd.read_csv(filename, sep=",", error_bad_lines=False, engine='python')
    pairs['awf'] = pairs['awf'].str.lower() + "/adj"
    pairs['nwf'] = pairs['nwf'].str.lower() + "/noun"
    pairs['count'] = 1
    pairs.dropna(inplace=True)
    pairs = pairs.drop_duplicates()
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
        if start_ents[d] > 0:
            if percentage:
                IG[d] = (start_ents[d] - H[d]) / start_ents[d]
            else:
                IG[d] = start_ents[d] - H[d]                
        else:
            IG[d] = 0
            
    return [IG['a'], IG['ab'], IG['b'], IG['ba']]

def score(triples, outfile):
        
    outfile = open(outfile, 'w')
    #outfile.write("order,a,b,n,abn,ban,anb,bna,nab,nba\n")
    outfile.write("key\tsurface\tmask\tattest\tig\n")

    # mask of corpus counts for each order type
    mask = []
    mask.extend(repeat(np.sum(triples.loc[triples[2].str.contains('/NOUN')]['count'].values)/2, 2))
    mask.extend(repeat(np.sum(triples.loc[triples[1].str.contains('/NOUN')]['count'].values)/2, 2))
    mask.extend(repeat(np.sum(triples.loc[triples[0].str.contains('/NOUN')]['count'].values)/2, 2))

    total = len(triples.key.unique())    

    print("scoring triples ...")
    for k,key in enumerate(triples.key.unique()):
        print_progress(k+1, total)
        w1 = key.split(',')[0]
        w2 = key.split(',')[1]
        w3 = key.split(',')[2]
        
        if "/noun" in w1:
            n = w1
            a = w2
            b = w3
        elif "/noun" in w2:
            a = w1
            n = w2
            b = w3
        else:
            a = w1
            b = w2
            n = w3

        #a = a.split('/')[0].lower()
        #b = b.split('/')[0].lower()
        #n = n.split('/')[0].lower()

        #c = np.sum(pairs['count'].values)
        #pa = np.sum(pairs.loc[pairs['awf'] == a]['count'].values) / c
        #pb = np.sum(pairs.loc[pairs['awf'] == b]['count'].values) / c
        #pn = np.sum(pairs.loc[pairs['nwf'] == n]['count'].values) / c

        an = np.sum(pairs.loc[(pairs['awf'] == a) & (pairs['nwf'] == n)]['count'].values)
        bn = np.sum(pairs.loc[(pairs['awf'] == b) & (pairs['nwf'] == n)]['count'].values)        
        
            
        # make sure adjs aren't the same and a/b/n are in pairs data
        if a != b and an > 0 and bn > 0:
            #pmi_a = log2(pan/pa)
            #pmi_b = log2(pbn/pb)
            
            igs_pre = partition(pairs, a, b, counts, None)
            igs_post = partition(pairs, a, b, counts, n.lower())

            surface = triples.loc[triples['key'] == key]
            igs = []
            perms = []
            masks = []

            # ig_abn
            igs.append(igs_pre[0] + igs_pre[1])
            s = ','.join([a,b,n])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])

            # ig_ban
            igs.append(igs_pre[2] + igs_pre[3])
            s = ','.join([b,a,n])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])
            
            # ig_anb
            igs.append(igs_pre[0] + igs_post[2])
            s = ','.join([a,n,b])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])

            # ig_bna
            igs.append(igs_pre[2] + igs_post[0])
            s = ','.join([b,n,a])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])

            # ig_nab            
            igs.append(igs_post[0] + igs_post[1])
            s = ','.join([n,a,b])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])

            # ig_nba
            igs.append(igs_post[2] + igs_post[3])
            s = ','.join([n,b,a])
            try:
                c = surface.loc[surface['surface'] == s]['count'].values[0]
                perms.append([s, c])
            except:
                perms.append([s, 0])

            ig_dist = np.array(igs)
            mask_dist = mask

            #try:
            #    pmi_ab = pmi_a/pmi_b
            #except:
            #    pmi_ab = 0
            #try:
            #    pmi_ba = pmi_b/pmi_a
            #except:
            #    pmi_ba = 0
            #pmi_dist = [pmi_ba, pmi_ab, 0, 0, pmi_ab, pmi_ba]                
            
            for i,perm in enumerate(perms):
                out = '\t'.join([key, perm[0], str(mask_dist[i]), str(perm[1]), str(ig_dist[i])])     
                outfile.write(out + "\n")

    outfile.close()
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition adjective space')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file of adj-noun pairs [awf,nwf]')    
    parser.add_argument('-t', '--triples', nargs=1, dest='triples', required=True, help='comma-delimited file of adj-adj-noun triples (no header)')
    args = parser.parse_args()

    print("loading pairs from " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])        
    counts = pd.pivot_table(pairs[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum).dropna()  

    print("load triples from " + args.triples[0] + " ...")
    triples = load_triples(args.triples[0])

    if 'triples' in args.triples[0]:
        outfile = args.triples[0].replace('triples', 'scores')
    else:
        outfile = "scores.csv"

    score(triples, outfile)
    print("\n")
