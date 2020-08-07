import argparse, sys
import pandas as pd
import numpy as np

from sklearn.metrics import plot_confusion_matrix
from matplotlib import pyplot as plt
#from sklearn.linear_model import LogisticRegression
#from sklearn.linear_model import LinearRegression
import seaborn as sns

from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
#from sklearn.metrics import confusion_matrix
import statsmodels.api as sm

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_scores(filename):
    print('loading and processing ' + filename + ' ...')
    scores = pd.read_csv(filename, sep="\t", error_bad_lines=False, engine='python').replace([np.inf, -np.inf], np.nan).dropna()
    scores['surface'] = scores['surface'].str.lower()
    templates = scores.template.unique()
    return scores, templates

def preprocess(scores, templates, run_all, metric):

    total = len(scores['key'].unique())
    cols = ['surface', 'template', 'attest', metric]

    x = {}
    y = {}

    xt = []
    yt = []

    for template in templates:
        x[template] = []
        y[template] = []

    for i,key in enumerate(scores['key'].unique()):
        print_progress(i+1, total)
        df = scores.loc[scores['key'] == key][cols].sort_values(by='surface')
        igs = df[metric].values

        if run_all:
            for i,row in df.iterrows():
                for j,row2 in df.iterrows():
                    if i!=j:
                        for k in range(np.sum(df['attest'])):
                            xt.append([row[metric] - row2[metric]])
                            yt.append(np.clip(row['attest'], 0, 1))
        
        for t,template in enumerate(templates):
            dist = df.loc[df['template'] == template]
            igs_t = dist[metric].values
            attests = dist.attest.values
            n = sum(attests)
            for i in range(n):
                try:
                    if igs_t[0] != igs_t[1]:
                        x[template].append([igs_t[0] - igs_t[1]])
                        y[template].append(np.clip(attests[0], 0, 1))
                except:
                    pass

    return x, y, np.array(xt), np.array(yt)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='evaluate scores')
    parser.add_argument('-tr', '--train', nargs=1, dest='train', required=True, help='tab-delimited scores file for training')
    parser.add_argument('-m', '--metric', nargs=1, dest='metric', required=True, help='metric [ig_sum or ig_ent]')    
    parser.add_argument('-te', '--test', nargs=1, dest='test', required=False, help='tab-delimited scores file for hold-out testing')
    parser.add_argument('--plot', dest='plot', default=False, action='store_true', required=False, help='make plots')
    parser.add_argument('--all', dest='run_all', default=False, action='store_true', required=False, help='run all')        
    args = parser.parse_args()

    metric = args.metric[0]
    
    train, templates = load_scores(args.train[0])
    x, y, xt, yt = preprocess(train, templates, args.run_all, metric)

    print('')    

    if args.run_all:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE('minority')
        x_sm, y_sm = smote.fit_sample(xt, yt)

        x_train, x_dev, y_train, y_dev = train_test_split(np.array(x_sm), np.array(y_sm), random_state=1)
        x_ = sm.add_constant(x_train)
        logit = sm.Logit(y_train, x_, missing='drop')                
        result = logit.fit()
        x_ = sm.add_constant(x_dev)            
        y_pred = result.predict(x_)
        print(result.summary())
        x_ = sm.add_constant(x_dev)                
        y_pred = result.predict(x_)
        logistic = True
    
        print("\nVALIDATING ...")
        print(classification_report(y_dev, np.digitize(y_pred, bins=[0.5])))

    try:
        test, test_templates = load_scores(args.test[0])
        x_test, y_test, xt_test, yt_test = preprocess(test, test_templates, args.run_all, metric)
        run_test = True
    except:
        run_test = False


    for t,template in enumerate(templates):
        if len(x[template]) > 7:
            print('\n' + template)

            print('TRAINING ...')
            x_train, x_dev, y_train, y_dev = train_test_split(np.array(x[template]), np.array(y[template]), random_state=1)
            
            try:
                x_ = sm.add_constant(x_train)
                logit = sm.Logit(y_train, x_, missing='drop')                
                result = logit.fit()
                #print(result.pred_table(threshold=0.5))
                x_ = sm.add_constant(x_dev)            
                y_pred = result.predict(x_)
                print(result.summary())

                x_ = sm.add_constant(x_dev)                
                y_pred = result.predict(x_)
                logistic = True
                print("\nVALIDATING ...")
                print(classification_report(y_dev, np.digitize(y_pred, bins=[0.5])))                
            except:
                print('not enough data')
                #model = sm.OLS(y_train, x_train).fit()
                #y_pred = model.predict(x_train)
                #print(model.summary())

                #y_pred = model.predict(x_dev)
                #logistic = False


            if args.plot:
                print("\nPLOTTING REGRESSION...")
                plt.figure(figsize=(9,6))
                sns.regplot(x_train, y_train, logistic=logistic, scatter=True, truncate=True, marker='|')
                plt.xlabel('delta IG')
                plt.ylabel('alphabetical')
                plt.title(template)
                plt.savefig(template + '_regression.png')
                plt.clf()

            if run_test and template in x_test:
                print("\nTESTING ...")
                x_ = sm.add_constant(x_test[template])
                y_pred = np.digitize(result.predict(x_), bins=[0.5])
                y_true = y_test[template]
                print(classification_report(y_true, y_pred))

                data = {'y_Actual':    y_true,
                        'y_Predicted': y_pred
                }

                df = pd.DataFrame(data, columns=['y_Actual','y_Predicted'])

                confusion_matrix = pd.crosstab(df['y_Actual'], df['y_Predicted'], rownames=['Actual'], colnames=['Predicted'])
                print (confusion_matrix)
                
                if args.plot:
                    print("\nPLOTTING CONFUSION ...")
                    sns.heatmap(confusion_matrix, annot=True, cmap=plt.cm.Blues, fmt=".0f")
                    plt.savefig(template + "_confusion.png")
                    plt.clf()
