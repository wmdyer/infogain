import argparse, sys
import pandas as pd
import numpy as np

from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import statsmodels.api as sm

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_scores(filename, verbose):
    if verbose:
        print('loading and processing ' + filename + ' ...')
    scores = pd.read_csv(filename, sep="\t", error_bad_lines=False, engine='python').replace([np.inf, -np.inf], np.nan).dropna()
    scores['clusters'] = scores['clusters'].str.lower()
    scores['attest'] = np.clip(scores['attest'], 0, 100)
    templates = scores.template.unique()
    return scores, templates

def preprocess(scores, templates, metric, verbose):

    total = len(scores['key'].unique())
    cols = ['clusters', 'template', 'attest', metric]

    x = {}
    y = {}

    for template in templates:
        x[template] = []
        y[template] = []

    for i,key in enumerate(scores['key'].unique()):
        if verbose:
            print_progress(i+1, total)
        df = scores.loc[scores['key'] == key][cols].sort_values(by='clusters')
        igs = df[metric].values
        
        for t,template in enumerate(templates):
            dist = df.loc[df['template'] == template]
            igs_t = dist[metric].values
            attests = dist.attest.values
            try:
                if igs_t[0] != igs_t[1]:
                    for i in range(attests[0]):
                        x[template].append([igs_t[0] - igs_t[1]])
                        y[template].append(1)                        
                    for i in range(attests[1]):
                        x[template].append([igs_t[0] - igs_t[1]])
                        y[template].append(0)
            except:
                pass

    return x, y

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='evaluate scores')
    parser.add_argument('-tr', '--train', nargs=1, dest='train', required=True, help='tab-delimited scores file for training')
    parser.add_argument('-m', '--metric', nargs=1, dest='metric', required=True, help='metric [ig_sum or ig_ent]')    
    parser.add_argument('-te', '--test', nargs=1, dest='test', required=False, help='tab-delimited scores file for hold-out testing')
    parser.add_argument('--verbose', dest='verbose', default=False, action='store_true', required=False, help='verbose')            
    args = parser.parse_args()

    metric = args.metric[0]

    verbose = args.verbose
        
    train, templates = load_scores(args.train[0], verbose)
    try:
        seq_length = str(len(train['key'].values[0].split(','))).replace('2', 'pairs').replace('3', 'triples')
    except:
        print(train['key'])
        exit()
        
    x, y = preprocess(train, templates, metric, verbose)
    if verbose:
        print('')
        
    try:
        if args.test[0] == args.train[0]:
            test = train
            test_templates = templates
            x_test = x
            y_test = y
        else:
            test, test_templates = load_scores(args.test[0], verbose)
            x_test, y_test = preprocess(test, test_templates, metric, verbose)
        run_test = True
    except Exception as e:
        run_test = False
    

    n_train = {}
    n_test = {}
    
    if verbose:
        print('')
    
    for t,template in enumerate(templates):
        n_train[template] = len(x[template])        
        if n_train[template] > 7:
            if verbose:
                print('\n' + template)
                print('TRAINING ...')
                x_train, x_dev, y_train, y_dev = train_test_split(np.array(x[template]), np.array(y[template]), random_state=1)
            else:
                x_train = np.array(x[template])
                y_train = np.array(y[template])
            
            try:
                x_ = sm.add_constant(x_train)
                logit = sm.Logit(y_train, x_, missing='drop')
                if verbose:
                    result = logit.fit()
                    print(result.summary())
                else:
                    result = logit.fit(disp=0)

                if not verbose:
                    print(metric, template, "beta_0", result.params[0])                    
                    print(metric, template, "beta_1", result.params[1])
                    print(metric, template, "p-value", result.pvalues[1])                    
                elif not run_test:
                    x_ = sm.add_constant(x_dev)
                    y_pred = result.predict(x_)
                    print("\nVALIDATING ...")
                    print(classification_report(y_dev, np.digitize(y_pred, bins=[0.5])))                    
            except:
                print('not enough data')

            if run_test and template in x_test:
                if verbose:
                    print("\nTESTING ...")
                n_test[template] = len(x_test[template])
                try:
                    x_ = sm.add_constant(x_test[template])
                    y_pred = np.digitize(result.predict(x_), bins=[0.5])
                    y_true = y_test[template]
                    if verbose:
                        print(classification_report(y_true, np.digitize(y_pred, bins=[0.5])))
                    else:
                        print(metric, template, "accuracy", accuracy_score(y_true, np.digitize(y_pred, bins=[0.5])))
                except:
                    pass

n_all = np.sum(list(n_train.values())) + np.sum(list(n_test.values()))
print(metric, 'all', 'n', n_all)
print(metric, 'all', 'n_train', np.sum(list(n_train.values())))
print(metric, 'all', 'n_test', np.sum(list(n_test.values())))

for key in n_train.keys():
    print(metric, key, "n_train", n_train[key], n_train[key]/np.sum(list(n_train.values())))

for key in n_test.keys():
    print(metric, key, "n_test", n_test[key], n_test[key]/np.sum(list(n_test.values())))

