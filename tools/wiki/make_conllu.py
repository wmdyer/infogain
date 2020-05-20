import sys, argparse, re
import pandas as pd
import numpy as np
from ufal.udpipe import Model, Pipeline, ProcessingError

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

#MAX_LEN = 900000
MAX_LEN = 100000

def load_text_data(filename):
    texts = []
    text = ""

    with open(filename) as fp:
        for i,line in enumerate(fp):
            if len(text) > MAX_LEN:
                texts.append(text)
                text = ""
            text += line
        texts.append(text)
    return texts

def process(pipeline, error, text):
    processed = pipeline.process(text, error)

    if error.occurred():
        print(error.message)
        exit()
    else:
        return processed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='align subtrees')
    parser.add_argument('-f', '--file', nargs=1, dest='f', required=True, help='text file')
    parser.add_argument('-m', '--model', nargs=1, dest='m', required=True, help='udpipe model')
    args = parser.parse_args()

    filename = args.f[0]

    print("loading data from " + filename + " ...")

    texts = load_text_data(filename)

    print("loading model from " + args.m[0] + " ...")    
    model = Model.load(args.m[0])    
    if not model:
        print("Can't load model " + args.m[0])
        exit()
    print("building pipeline ...")
    pipeline = Pipeline(model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    error = ProcessingError()

    # reset conllu
    print("resetting output file " + filename + ".conllu ...")
    outfile = open(filename + ".conllu", "a")
    outfile.write("")    
    outfile.close()
    
    total = len(texts)
    for i,text in enumerate(texts):
        print_progress(i, total)
        outfile = open(filename + ".conllu", "a")
        processed = process(pipeline, error, text)
        outfile.write(processed)
        outfile.close()

    print("")

