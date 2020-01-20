import pandas as pd
import numpy as np
import sys

def load_ud_file(filename):
    ud = pd.read_csv(filename, sep="\t",error_bad_lines=False, engine='python', header=None, comment= '#', quoting=3)
    #ud.columns = ['idx', 'wordform', 'lemma', 'ud_pos', 'sd_pos', 'morph', 'head', 'rel1', 'rel2', 'other']
    return ud

def extract_triples(df):
    triples = []
    chunksize = 3
    chunk = [x[:] for x in [[None] * df.shape[1]] * chunksize]
    codes = {'ADJ': 1, 'NOUN': 2}
    for index, row in df.iterrows():
        chunk[2] = row
        try:
            pos = codes[chunk[0][3]] + codes[chunk[1][3]] + codes[chunk[2][3]] == 4
            tree = (chunk[0][6] == chunk[1][6] and chunk[0][6] == chunk[2][0]) or (chunk[0][6] == chunk[2][6] and chunk[0][6] == chunk[1][0]) or (chunk[1][6] == chunk[2][6] and chunk[1][6] == chunk[0][0])
            
            if pos and tree:
                triples.append([str(chunk[0][1]).lower() + "/" + str(chunk[0][3]), str(chunk[1][1]).lower() + "/" + str(chunk[1][3]), str(chunk[2][1]).lower() + "/" + str(chunk[2][3])])
        except:
            pass

        chunk[0] = chunk[1]
        chunk[1] = chunk[2]

    return triples

print("load UD data from " + sys.argv[1] + "...")
ud = load_ud_file(sys.argv[1])

print("extract triples...")
triples = extract_triples(ud)

outfile = open("triples.csv", "w")

AAN = 0
ANA = 0
NAA = 0
for triple in triples:
    if "/NOUN" in triple[0]:
        NAA+=1
    elif "/NOUN" in triple[1]:
        ANA+=1
    else:
        AAN+=1        
    outfile.write(str(triple[0]) + "," + str(triple[1]) + "," + str(triple[2]) + "\n")
outfile.close()

print("AAN: " + str(AAN))
print("ANA: " + str(ANA))
print("NAA: " + str(NAA))
