import sys
import pandas as pd
import numpy as np
from scipy.stats import entropy
import argparse

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_triples(filename):
    triples = pd.read_csv(filename, sep=",", header=None)
    return triples

def load_pairs(filename):
    pairs = pd.read_csv(filename, sep=",")
    pairs['count'] = 1
    pairs.dropna(inplace=True)
    return pairs

def partition(pairs, a, b, counts, n):

    percentage = True
    
    nouns_a = pairs.loc[pairs['awf'] == a]['nwf']
    adjs_a = pairs.loc[pairs['nwf'].isin(nouns_a)]
    adjs_a = pd.pivot_table(adjs_a[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum)

    nouns_b = pairs.loc[pairs['awf'] == b]['nwf']
    adjs_b = pairs.loc[pairs['nwf'].isin(nouns_b)]
    adjs_b = pd.pivot_table(adjs_b[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum)

    if n != None:
        adjs_n = pairs.loc[pairs['nwf'] == n]['awf']
    else:
        adjs_n = pairs.loc[(pairs['nwf'].isin(nouns_a.values)) | (pairs['nwf'].isin(nouns_b.values))]['awf']

    adjs = pd.merge(adjs_a, adjs_n, how='right', left_on=['awf'], right_on=['awf']).fillna(0).drop_duplicates()
    dfa = pd.merge(adjs, counts, how='left', left_on=['awf'], right_index=True).fillna(0).drop_duplicates()
        
    adjs = pd.merge(adjs_b, adjs_n, how='right', left_on=['awf'], right_on=['awf']).fillna(0).drop_duplicates()
    dfb = pd.merge(adjs, counts, how='left', left_on=['awf'], right_index=True).fillna(0).drop_duplicates()

    dfa.set_index('awf', inplace=True)
    dfb.set_index('awf', inplace=True)

    try:
        dfa['pa'] = dfa['count_x']
        dfa['pac'] = (dfa['count_y'] - dfa['count_x'])
        
        dfb['pb'] = dfb['count_x']
        dfb['pbc'] = (dfb['count_y'] - dfb['count_x'])
        
        dfa['pab'] = dfa['pa'] * (dfb['count_x']/dfb['count_y'])
        dfa['pabc'] = dfa['pa'] * ((dfb['count_y'] - dfb['count_x'])/dfb['count_y'])
        
        dfb['pba'] = dfb['pb'] * (dfa['count_x']/dfa['count_y'])
        dfb['pbac'] = dfb['pb'] * ((dfa['count_y'] - dfa['count_x'])/dfa['count_y'])
                
        pa = np.nan_to_num(dfa['pa'].values, 0)
        pac = np.nan_to_num(dfa['pac'].values, 0)
        pab = np.nan_to_num(dfa['pab'].values, 0)
        pabc = np.nan_to_num(dfa['pabc'].values, 0)
        
        pb = np.nan_to_num(dfb['pb'].values, 0)
        pbc = np.nan_to_num(dfb['pbc'].values, 0)
        pba = np.nan_to_num(dfb['pba'].values, 0)
        pbac = np.nan_to_num(dfb['pbac'].values, 0)
        
        npa = np.sum(pa)
        npac = np.sum(pac)
        na = npa + npac
        
        npab = np.sum(pab)
        npabc = np.sum(pabc)
        nab = npab + npabc
        
        npb = np.sum(pb)
        npbc = np.sum(pbc)
        nb = npb + npbc
        
        npba = np.sum(pba)
        npbac = np.sum(pbac)
        nba = npba + npbac
        
        ent_a = entropy(dfa['count_y'].values, base=2)
        ent_b = entropy(dfb['count_y'].values, base=2)
        
        ent_ab = entropy(dfa['count_x'].values, base=2)
        ent_ba = entropy(dfb['count_x'].values, base=2)           
        
        Ia = (npa/na) * entropy(list(pa), base=2) + (npac/na) * entropy(list(pac), base=2)
        iga1 = (ent_a - Ia)
        
        Iab = (npab/nab) * entropy(list(pab), base=2) + (npabc/nab) * entropy(list(pabc), base=2)
        iga2 = (ent_ab - Iab)
        
        Ib = (npb/nb) * entropy(list(pb), base=2) + (npbc/nb) * entropy(list(pbc), base=2)
        igb1 = (ent_b - Ib)
        
        Iba = (npba/nba) * entropy(list(pba), base=2) + (npbac/nba) * entropy(list(pbac), base=2)
        igb2 = (ent_ba - Iba)

        if percentage:
            iga1 = iga1/ent_a
            iga2 = iga2/ent_ab
            igb1 = igb1/ent_b
            igb2 = igb2/ent_ba
                
        return [iga1, iga2, igb1, igb2]
    except:
        return [0, 0, 0, 0]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='partition')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file of count-adj-noun pairs')    
    parser.add_argument('-t', '--triples', nargs=1, dest='triples', required=True, help='comma-delimited file of adj-adj-noun triples')
    args = parser.parse_args()

    print("loading pairs from " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])        
    counts = pd.pivot_table(pairs[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum).dropna()  

    print("loading triples from " + args.triples[0] + " ...")
    triples = load_triples(args.triples[0])

    outfile = args.triples[0].split('_')[0] + "_scores.csv"
    outfile = open(outfile, 'w')

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

        a = a.split('/')[0]
        b = b.split('/')[0]
        n = n.split('/')[0]        

        igs_pre = partition(pairs, a, b, counts, None)
        igs_post = partition(pairs, a, b, counts, n)
        
        out = '\t'.join([order, a, b, n] + list(map(str, igs_pre)) + list(map(str, igs_post)))
            
        print(str(i+1) + "/" + str(total), out)
        outfile.write(out + "\n")



    outfile.close()
    
