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

def load_test_data(filename):
    df = pd.read_csv(filename, sep=",", dtype=str, header=None)
    return df

def post(a, b, n, counts, pairs):
    if '.' in a:
        atype = 'acl'
        ntype = 'ncl'
    else:    
        atype = 'awf'
        ntype = 'nwf'

    #n = None

    if n != None:
        adj_list = pairs.loc[pairs[ntype] == n][atype].drop_duplicates()
    else:
        adj_list = pairs.loc[(pairs[ntype] == n) | (pairs[ntype] != n)][atype].drop_duplicates()

    ha = counts[counts.index.isin(adj_list)]
    hn = np.sum(ha['count'].values)    
    h = entropy(ha['count'].values, base=2)

    noun_list_a = pairs[pairs[ntype].isin(pairs.loc[(pairs[atype] == a)][ntype].values)][ntype].drop_duplicates()
    noun_list_b = pairs[pairs[ntype].isin(pairs.loc[(pairs[atype] == b)][ntype].values)][ntype].drop_duplicates()
    
    if n != None:
        adj_a = pd.merge(pd.merge(pairs, adj_list), noun_list_a)
        adj_b = pd.merge(pd.merge(pairs, adj_list), noun_list_b)
    else:
        adj_a = pd.merge(pairs, noun_list_a)
        adj_b = pd.merge(pairs, noun_list_b)        

    aa = pd.pivot_table(adj_a, index=[atype], values=['count', atype], aggfunc=np.sum)
    #aac = counts[counts.index.isin(adj_list)].sub(aa, fill_value=0)

    ab = pd.pivot_table(adj_b, index=[atype], values=['count', atype], aggfunc=np.sum)
    #abc = counts[counts.index.isin(adj_list)].sub(ab, fill_value=0)


    aa.loc[a]['count'] = 0
    aa = aa.divide(counts[counts.index.isin(adj_list)]['count'], axis=0)

    #aa = aa.divide(np.sum(aa['count'].values))['count']
    #aac = aac.divide(counts[counts.index.isin(adj_list)]['count'], axis=0)

    ab.loc[b]['count'] = 0
    ab = ab.divide(counts[counts.index.isin(adj_list)]['count'], axis=0)
    
    #abc = abc.divide(counts[counts.index.isin(adj_list)]['count'], axis=0)
    #ab = ab.divide(np.sum(ab['count'].values))['count']    

    #print(aa)
    #print(ab)
    #exit()
    #print(np.sum(ab['count'].values))
    #exit()

    #print("\n" + b)
    #print(ab)
    #print(abc)
    #exit()

    #return entropy(aac['count'].values, qk=aa['count'].values, base=2), entropy(abc['count'].values, qk=ab['count'].values, base=2)
    #return np.sum(aa['count'].values), np.sum(ab['count'].values)

    #ent_a = 0
    #for p in [aa, aac]:
    #    n = np.sum(p['count'].values)        
    #    if n > 0:
    #        ent_a += (n/hn) * entropy(p['count'].values, base=2)

    #ent_b = 0
    #for p in [ab, abc]:
    #    n = np.sum(p['count'].values)        
    #    if n > 0:
    #        ent_b += (n/hn) * entropy(p['count'].values, base=2)

    #return h-ent_a, h-ent_b
    return entropy(aa.values, base=2), entropy(ab.values, base=2)


def post2(a, b, n, counts, pairs):
    if '.' in a:
        atype = 'acl'
        ntype = 'ncl'
    else:    
        atype = 'awf'
        ntype = 'nwf'

        
    adj_list = pairs.loc[pairs[ntype] == n][atype].drop_duplicates()
    #adj_list = pairs[atype].drop_duplicates()
    ha = counts[counts.index.isin(adj_list)]
    hn = entropy(ha['count'].values, base=2)
    
    ig = []

    for order in [[a,b], [b,a]]:
        noun_list_a = pairs[pairs[ntype].isin(pairs.loc[(pairs[atype] == order[0])][ntype].values)][ntype].drop_duplicates()
        adj_a = pd.merge(pd.merge(pairs, adj_list), noun_list_a)
        #print(adj_a)

        aa = pd.pivot_table(adj_a, index=[atype], values=['count', atype], aggfunc=np.sum)

        fa = aa.loc[order[0]]['count']
        aac = counts[counts.index.isin(adj_list)].sub(aa, fill_value=0)

        
        noun_list_b = pairs[pairs[ntype].isin(pairs.loc[(pairs[atype] == order[1])][ntype].values)][ntype].drop_duplicates()
        adj_b = pd.merge(pd.merge(adj_a, adj_list), noun_list_b)
        aab = pd.pivot_table(adj_b, index=[atype], values=['count', atype], aggfunc=np.sum)

        #aa.loc[order[0]]['count'] = counts.loc[order[0]]['count']
        #aab.loc[order[0]]['count'] = counts.loc[order[0]]['count']
        #aab.loc[order[1]]['count'] = counts.loc[order[1]]['count']

        
        aabc = aa - aab
        aacbc = aac - aab
        #aacbc.loc[aacbc['count'] < 0] = 0
        aacb = aac - aacbc

        print(aa)
        print(aac)
        exit()

        if 1 == 2:
            if np.sum(aab['count'].values) > 0:
                ig.append((np.sum(aab['count'].values)/np.sum(ha['count'].values)) * entropy(aab['count'].values, base=2))
            else:
                ig.append(0)
            if np.sum(aabc['count'].values) > 0:
                ig.append((np.sum(aabc['count'].values)/np.sum(ha['count'].values)) * entropy(aabc['count'].values, base=2))
            else:
                ig.append(0)
            if np.sum(aacb['count'].values) > 0:
                ig.append((np.sum(aacb['count'].values)/np.sum(ha['count'].values)) * entropy(aacb['count'].values, base=2))
            else:
                ig.append(0)
            if np.sum(aacbc['count'].values) > 0:
                ig.append((np.sum(aacbc['count'].values)/np.sum(ha['count'].values)) * entropy(aacbc['count'].values, base=2))
            else:
                ig.append(0)
        else:
            ig.append((np.sum(aa['count'].values)/np.sum(ha['count'].values)) * entropy(aa['count'].values, base=2) + (np.sum(aac['count'].values)/np.sum(ha['count'].values)) * entropy(aac['count'].values, base=2))

        #print(order)
        #print(np.sum(ha['count'].values))
        #print(np.sum(aa['count'].values) + np.sum(aac['count'].values))
        #print(np.sum(aab['count'].values) + np.sum(aabc['count'].values) + np.sum(aacb['count'].values) + np.sum(aacbc['count'].values))
        #print(np.sum(aa['count'].values))
        #print(np.sum(aab['count'].values) + np.sum(aabc['count'].values))

        #print(np.sum(aac['count'].values))
        #print(np.sum(aacb['count'].values) + np.sum(aacbc['count'].values))        
        #print(aab)
        #print(aabc)


        #ig.append(entropy(aa['count'].values, qk=ha['count'].values, base=2))
        #ig.append(entropy(aab['count'].values, qk=aa['count'].values, base=2))
        #ig.append(entropy(aab['count'].values, qk=ha['count'].values, base=2))        

        #ig.append((np.sum(aa['count'].values)/np.sum(ha['count'].values)) * entropy(aa['count'].values, base=2))
        #print(aab)
        #ig.append((np.sum(aab['count'].values)/np.sum(ha['count'].values)) * entropy(aab['count'].values, base=2))
        #print(n)
        #exit()        
        
        #ig.append(fa)
        #ig.append(hn - ((na/n) * entropy(aa_dist, base=2) + (nac/n) * entropy(aac_dist, base=2)))
        #ig.append((na/n) * entropy(aa_dist, base=2))
        
        #return ig[0], ig[1], ig[2], ig[3]

        #ig.append(entropy(aa['count'].values, base=2))
        #ig.append(entropy(aab['count'].values, base=2))
    return ig
    
            
if __name__ == '__main__':
    # awf = adjective wordform
    # acl = adjective cluster
    # nwf = noun wordform
    # ncl = noun cluster
    
    parser = argparse.ArgumentParser(description='score adj pairs')
    parser.add_argument('-p', '--pairs', nargs=1, dest='pairs', required=True, help='comma-delimited file containing [count,awf,nwf,acl,ncl] for calculating predictors')
    parser.add_argument('-t', '--test', nargs=1, dest='test_file', required=True, help='comma-delimited file containing [count,adj1_word,adj2_word,noun_word] for test')
    args = parser.parse_args()
    
    #print("loading pairs data from " + args.pairs[0] + " ...")
    pairs = load_pairs(args.pairs[0])

    #print("making cluster dicts ...")
    if 'acl' in pairs.columns:
        adf = pairs[['awf', 'acl']]
        acls = adf.set_index(['awf']).to_dict()['acl']
        ndf = pairs[['nwf', 'ncl']]
        ncls = ndf.set_index(['nwf']).to_dict()['ncl']

    test_data = load_test_data(args.test_file[0])

    awf_counts = pd.pivot_table(pairs[['count', 'awf']], index=['awf'], values=['count', 'awf'], aggfunc=np.sum)
    nwf_counts = pd.pivot_table(pairs[['count', 'nwf']], index=['nwf'], values=['count', 'nwf'], aggfunc=np.sum)

    if 'acl' in pairs.columns:
        acl_counts = pd.pivot_table(pairs[['count', 'acl']], index=['acl'], values=['count', 'acl'], aggfunc=np.sum)
        ncl_counts = pd.pivot_table(pairs[['count', 'ncl']], index=['ncl'], values=['count', 'ncl'], aggfunc=np.sum)

    outfile = open("scores.csv", 'w')
    outfile.write("ord,n,a,b,ia,ib\n")
    n = len(test_data)
    for i,triple in test_data.iterrows():
        if n > 10: print_progress(i+1, n)
        if "/NOUN" in triple.values[0]:
            nwf = triple.values[0]
            awf1 = triple.values[1]
            awf2 = triple.values[2]
            order = "nab"
        elif "/NOUN" in triple.values[1]:
            awf1 = triple.values[0]
            nwf = triple.values[1]
            awf2 = triple.values[2]
            order = "anb"
        else:
            awf1 = triple.values[0]
            awf2 = triple.values[1]
            nwf = triple.values[2]
            order = "abn"
        #try:
        if 'acl' in pairs.columns:
            try:
                acl1 = acls[awf1.lower()]
                acl2 = acls[awf2.lower()]
                ncl = ncls[nwf.lower()]

                kl1, kl2 = post(acl1, acl2, ncl, acl_counts, pairs[['count', 'acl', 'ncl']])
                outfile.write(order + "," + nwf + "," + awf1 + "," + awf2 + "," + str(kl1) + "," + str(kl2) + "\n")
            except:
                pass
        else:
            kl1, kl2 = post(awf1.lower(), awf2.lower(), nwf.lower(), awf_counts, pairs)
            outfile.write(order + "," + nwf + "," + awf1 + "," + awf2 + "," + str(kl1) + "," + str(kl2) + "\n")                        
    outfile.close()
    
print("")
