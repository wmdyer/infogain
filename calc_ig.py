import sys, codecs, os, math, argparse
import pandas as pd
import numpy as np
from scipy.stats import entropy
from collections import Counter

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_pairs(filename):
    pairs = pd.read_csv(filename, sep=",", dtype=str)
    pairs['awf'] = pairs['awf'].str.lower()
    pairs['nwf'] = pairs['nwf'].str.lower()
    pairs['count'] = pd.to_numeric(pairs['count'])
    return pairs

def load_test_data(filename, pair_acls, pair_ncls):
    test_data = {}
    awfs = []
    nwfs = []
    acls = []
    ncls = []
    df = pd.read_csv(filename, sep=",", dtype=str)[['count', 'adj1_word', 'adj2_word', 'noun_word']]
    for w in ['noun_word', 'adj1_word', 'adj2_word']:
        df[w] = df[w].str.lower()
    df['count'] = pd.to_numeric(df['count'])
    df = df.fillna('null') # treat instances of 'null' in df as strings, not NULL
    test_data['triples'] = df.values.tolist()
    test_data['awfs'] = np.unique(df[['adj1_word', 'adj2_word']].values)
    test_data['nwfs'] = np.unique(df['noun_word'].values)
    test_data['acls'] = pd.merge(pd.DataFrame(test_data['awfs']), pd.DataFrame.from_dict(pair_acls, orient='index'), how='inner', left_on=[0], right_index=True)['0_y'].unique()
    test_data['ncls'] = pd.merge(pd.DataFrame(test_data['nwfs']), pd.DataFrame.from_dict(pair_ncls, orient='index'), how='inner', left_on=[0], right_index=True)['0_y'].unique()

    return test_data

def load_vectors(filename):
    df = pd.read_csv(filename, sep='["]* ["]*', header=None, error_bad_lines=False, engine='python')
    return df

def load_subj(filename):
    df = pd.read_csv(filename, sep=",")
    return df

def calc_pmi(pxy, px):
    #return math.log(pxy/px,2)
    return pxy-px

def info_theory(d, n, start_ent):
    integ_cost = {}
    info_gain = {}
    for k in d:
        dist = list(Counter(d[k]).values())
        ent = entropy(dist, base=2)
        integ_cost[k] = ent
        info_gain[k] = start_ent - (len(dist)/n) * ent
    return integ_cost, info_gain
        
if __name__ == '__main__':
    # awf = adjective wordform
    # acl = adjective cluster
    # nwf = noun wordform
    # ncl = noun cluster
    
    parser = argparse.ArgumentParser(description='score adj pairs')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file containing [count,awf,nwf,acl,ncl] for calculating predictors')
    parser.add_argument('-t', '--test', nargs=1, dest='test_file', required=True, help='comma-delimited file containing [count,adj1_word,adj2_word,noun_word] for test')
    args = parser.parse_args()
    
    print("loading pairs data from " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])

    print("making cluster dicts ...")
    adf = pairs[['awf', 'acl']]
    acls = adf.set_index(['awf']).to_dict()['acl']
    ndf = pairs[['nwf', 'ncl']]
    ncls = ndf.set_index(['nwf']).to_dict()['ncl']

    print("loading test data from " + args.test_file[0] + " ...")
    test_data = load_test_data(args.test_file[0], acls, ncls)

    print("loading subjectivities ...")
    subjectivities = load_subj(args.subj[0])[['predicate', 'response']].set_index('predicate')
    subj = subjectivities.to_dict()['response']

    print("adding pairs to dataframe ...")
    pairs['awf_nwf'] = pairs['awf'] + "_" + pairs['nwf']
    pairs['awf_ncl'] = pairs['awf'] + "_" + pairs['ncl']
    pairs['acl_nwf'] = pairs['acl'] + "_" + pairs['nwf']
    pairs['acl_ncl'] = pairs['acl'] + "_" + pairs['ncl']

    print("expanding pairs ...")
    pairs = pairs.reindex(pairs.index.repeat(pairs['count']))
    del pairs['count']

    print("mapping adj to nouns ...")
    print(" -awf_to_nwfs")
    awf_to_nwfs = {k: g["nwf"].tolist() for k,g in pairs.loc[pairs['awf'].isin(test_data['awfs'])].groupby('awf')}

    print(" -acl_to_ncls")
    acl_to_ncls = {k: g["ncl"].tolist() for k,g in pairs.loc[pairs['acl'].isin(test_data['acls'])].groupby('acl')}

    print("mapping nouns to adjs ...")
    print(" -nwf_to_awfs")
    nwf_to_awfs = {k: g["awf"].tolist() for k,g in pairs.loc[pairs['nwf'].isin(test_data['nwfs'])].groupby('nwf')}

    print(" -ncl_to_acls")
    ncl_to_acls = {k: g["acl"].tolist() for k,g in pairs.loc[pairs['ncl'].isin(test_data['ncls'])].groupby('ncl')}

    print("calculating entropies ...")
    print(" -starting")
    start_ent_nwf = entropy(list(Counter(pairs['nwf'].values).values()), base=2)
    start_ent_ncl = entropy(list(Counter(pairs['ncl'].values).values()), base=2)
    start_ent_awf = entropy(list(Counter(pairs['awf'].values).values()), base=2)
    start_ent_acl = entropy(list(Counter(pairs['acl'].values).values()), base=2)
    n_nwf = len(pairs.nwf.unique())
    n_ncl = len(pairs.ncl.unique())
    n_awf = len(pairs.awf.unique())
    n_acl = len(pairs.acl.unique())
    
    print(" -awf_pre")
    awf_pre_igs = partition_N(awf_to_nwfs, n_nwf, start_ent_nwf)

    print(" -acl_pre")
    acl_pre_igs = partition_N(acl_to_ncls, n_ncl, start_ent_ncl)

    print(" -awf_post")
    awf_post_igs = partition_A(awf_to_nwfs, n_awf, start_ent_awf)

    print(" -acl_post")
    acl_post_igs = partition_A(acl_to_ncls, n_acl, start_ent_acl)    

    print("printing output to scores.csv ...")
    outfile = open("scores.csv", 'w')
    outfile.write("id,idx,count,awf,nwf,acl,ncl,awf_pre_ig,acl_pre_ig,awf_post_ig,acl_post_ig\n"
    n = len(test_data['triples'])
    for i, triple in enumerate(test_data['triples']):
        print_progress(i+1, n)
        nwf = triple[3]
        ncl = None
        try:
            ncl = str(ncls[nwf])
        except:
            pass
        for j, awf in enumerate(triple[1:3]):
            acl = None
            try:
                acl = str(acls[awf])
            except:
                pass

            # info gain
            awf_pre_ig = None
            acl_pre_ig = None
            awf_post_ig = None
            acl_post_ig = None
            try:
                awf_pre_ig = awf_pre_igs[awf]
            except:
                pass
            try:
                acl_pre_ig = acl_pre_igs[acl]
            except:
                pass
            try:
                awf_post_ig = awf_post_igs[awf]
            except:
                pass
            try:
                acl_post_ig = acl_post_igs[acl]
            except:
                pass                  

            outfile.write(str(i) + "," + str(j) + "," + str(triple[0]) + "," + awf + "," + nwf + "," + str(acl) + "," + str(ncl) + "," + str(awf_pre_ig) + "," + str(acl_pre_ig) + "," + str(awf_post_ig) + "," + str(acl_post_ig) + "\n")
                
    outfile.close()
    
print("")
