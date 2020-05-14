import argparse, sys
import spacy_udpipe
from collections import Counter
import pandas as pd
import numpy as np

MAX_LEN = 900000

def print_progress(i, n):
    j = (i+1) / n
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%% N %d/%d " % ('='*int(20*j), 100*j, i, n))
    sys.stdout.flush()
    return i + 1

def load_file(filename):
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

def parse(lang, texts):

    try:
        nlp = spacy_udpipe.load(lang)
    except:
        spacy_udpipe.download(lang)
        nlp = spacy_udpipe.load(lang)

    chunks = len(texts)
    for i,text in enumerate(texts):
        print("parsing chunk " + str(i+1) + "/" + str(chunks) + " ...")
        an_pairs = []
        doc = nlp(text)
        #total = len(doc.sents)

        for j, sent in enumerate(doc.sents):
            #print_progress(j+1, total)
            noun_heads = {}
            for token in sent:
                if token.pos_ == 'ADJ' and token.head.pos_ == 'NOUN' and token.dep_ == 'amod':
                    text = token.lemma_
                    if text == "_":
                        text = token.text
                    head = token.head.lemma_
                    if head == "_":
                        head = token.head.text
                    an_pairs.append([text.lower(), head.lower()])

                    try:
                        noun_heads[head].add(text.lower())
                    except:
                        noun_heads[head] = {text.lower()}

        df = pd.DataFrame(an_pairs)
        df.to_csv("raw_an_pairs.csv", mode='a', sep=',', encoding='utf-8', index=False, header=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='align subtrees')
    parser.add_argument('-f', '--file', nargs=1, dest='f', required=True, help='text file')
    parser.add_argument('-l', '--language', nargs=1, dest='l', required=True, help='language code')
    args = parser.parse_args()
    
    filename = args.f[0]
    lang = args.l[0]
    
    print("loading " + filename + " ...")
    texts = load_file(filename)

    # reset output file
    outfile = open('raw_an_pairs.csv', 'w')
    outfile.write("")
    outfile.close()
    
    parse(lang, texts)
    

    
