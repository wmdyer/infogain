import sys
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import argparse

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_forms(filename):
    df = pd.read_csv(filename, sep="\t", header=None).drop_duplicates()
    df.columns = ['lemma', 'wfs']
    return df

def load_vectors(filename, c):
    df = pd.read_csv(filename, sep='["]* ["]*', header=None, error_bad_lines=False, engine='python', index_col=0)
    if c != 1.0:
        print("running pca(" + str(c) + ") ...")
        x = run_pca(df.values, c)
        w = df.index
        df = pd.concat([pd.DataFrame(w), pd.DataFrame(x)], axis=1, ignore_index=True)
        df.set_index([0], inplace=True)
    return df

def run_pca(x, c):
    xdim = x.shape[1]
    pca = PCA(c)
    x = StandardScaler().fit_transform(x)
    principalComponents = pca.fit_transform(x)
    print("  dim: " + str(xdim) + " -> " + str(pca.n_components_))
    return principalComponents

def get_clusters(words, vectors, k):
    kmeans_model = KMeans(init='k-means++', n_clusters=k, n_init=10, max_iter=100)
    kmeans_model.fit(vectors)
    labels = kmeans_model.labels_

    clusters = {}

    for i, word in enumerate(words['lemma'].values):
        clusters[word] = int(labels[i])

    return clusters
        
def combine_vectors(forms, vectors):

    single_forms = forms[forms['wfs'].str.contains(',') == False].drop_duplicates()
    multi_forms = forms[forms['wfs'].str.contains(',', na=False)].drop_duplicates()

    print('extracting lemma vectors ...')
    wv = pd.merge(single_forms, vectors, left_on=['lemma'], right_index=True)
    c_forms = wv['lemma'].values.tolist()
    c_vectors = np.array(wv[wv.columns[2:]].values).astype(float).tolist()

    print('combining wordform vectors ...')
    total = len(multi_forms.lemma.unique())
    j=1
    for i,row in multi_forms.iterrows():
        j = print_progress(j, total)
        wv = vectors.loc[vectors.index.isin(str(row['wfs']).split(','))]
        vec = np.sum(wv.values, axis=0)/wv.values.shape[1]
        c_forms.append(row['lemma'])
        c_vectors.append(np.squeeze(vec))

    forms = pd.DataFrame(c_forms)
    vectors = pd.DataFrame(c_vectors)

    forms.columns = ['lemma']

    return forms, vectors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='k-means cluster words based on embeddings')
    parser.add_argument('-v', '--vectors', nargs=1, dest='vectors', required=True, help='GloVe file containing word vectors')
    parser.add_argument('-f', '--forms', nargs=1, dest='forms', required=True, help='file containing tab-delimited [lemma wordforms]')
    parser.add_argument('-k', nargs=1, dest='k', required=False, help='k value for clustering; default is 300')
    parser.add_argument('-c', nargs=1, dest='c', type=float, required=False, help='pct of components to keep after pca; default is 1.0 (all)')
    args = parser.parse_args()

    try:
        k = int(args.k[0])
    except:
        k = 300
    try:
        c = args.c[0]
    except:
        c = 1.0

    print("loading forms ...")
    forms = load_forms(args.forms[0])

    print("loading vectors ...")
    vectors = load_vectors(args.vectors[0], c)

    words, vectors = combine_vectors(forms, vectors)

    print('')
    
    print("clustering (k=" + str(k) + ") ...")
    cls = get_clusters(words, vectors, k)
    words['cl'] = words['lemma'].map(cls).astype('str')
    words = words.loc[words['cl'] != 'nan']

    print("printing output to clusters.csv ...")
    outfile = open("clusters.csv", 'w')
    outfile.write(words.to_csv(columns=['lemma', 'cl'], index=False))
    outfile.close()
    
