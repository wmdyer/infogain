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

def load_words(filename):
    words = pd.read_csv(filename, sep=",", header=None)
    words.columns = ['wf']
    words['wf'] = words['wf'].str.lower()
    words = words.drop_duplicates()
    return words

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
#    pca = PCA(c)
    pca = PCA(c * xdim)
    x = StandardScaler().fit_transform(x)
    principalComponents = pca.fit_transform(x)
#    print(principalComponents.explained_variance_ratio_.cumsum())
    print("  dim: " + str(xdim) + " -> " + str(pca.n_components_))
    return principalComponents

def get_clusters(words, vectors, k):
    kmeans_model = KMeans(init='k-means++', n_clusters=k, n_init=10, max_iter=100)
    kmeans_model.fit(vectors)
    labels = kmeans_model.labels_

    clusters = {}

    for i, word in enumerate(words['wf'].values):
        clusters[word] = int(labels[i])

    return clusters
        
def extract_vectors(words, vectors):
    wv = pd.merge(pd.DataFrame(words.wf.unique()), vectors, left_on=[0], right_index=True)
    word_vectors = np.array(wv[wv.columns[1:]].values).astype(float)

    words = pd.DataFrame(wv[0])
    words.columns = ['wf']

    return words, word_vectors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='k-means cluster words based on embeddings')
    parser.add_argument('-v', '--vectors', nargs=1, dest='vectors', required=True, help='GloVe file containing word vectors')
    parser.add_argument('-w', '--words', nargs=1, dest='words', required=True, help='file containing words')
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

    print("loading words from " + args.words[0] + " ...")
    words = load_words(args.words[0])

    print("loading vectors from " + args.vectors[0] + " ...")
    vectors = load_vectors(args.vectors[0], c)

    print("extracting vectors ...")
    words, word_vectors = extract_vectors(words, vectors)

    print("clustering (k=" + str(k) + ") ...")
    cls = get_clusters(words, word_vectors, k)
    words['cl'] = words['wf'].map(cls).astype('str')
    words = words.loc[words['cl'] != 'nan']

    print("printing output to clusters.csv ...")
    outfile = open("clusters.csv", 'w')
    outfile.write(words.to_csv(columns=['wf', 'cl'], index=False))
    outfile.close()
