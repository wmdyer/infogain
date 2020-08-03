# infogain
using information gain to describe adj order

## using pre-trained model
```{bash}
cd data/fr
python ../../src/test.py -s triples.csv
python ../../src/regress.py -tr scores.tsv -m ig_ent
```

## source data

*CoNLLU files*

 >[CoNLL 2017 Shared Task - Automatically Annotated Raw Texts and Word Embeddings](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1989)
 
 >[Universal Dependencies](https://github.com/UniversalDependencies)

*Word embeddings*

 >[fastText](https://fasttext.cc/docs/en/crawl-vectors.html)


## training
*1. extract NPs from conllu file*
```{bash}
./tools/extract_conllu_nps.sh <file>.conllu
```

*2. cluster (optional)*
```{bash}
cat nps.tsv | cut -f2,3 | tr '\t,' '\n' | sort -u > words
join <(cat words | sort -k1,1) <(cat <vectors> | sort -k1,1) > vecs
python ./src/cluster.py -v vecs -w words [-k <num_clusters>] [-c <pct_pca>]
```

*3. train*
```{bash}
python ./src/train.py -n nps.tsv [-c clusters.csv] [-fn 100] [-fl -1]
```

## testing

*test on AN/NA pairs*
```{bash}
./tools/extract_conllu_pairs.sh <file>.conllu
python ./src/test.py -s <file>.csv
mv scores.tsv scores_pairs.tsv
```

*test on AAN triples*
```{bash}
./tools/extract_conllu_triples.sh <file>.conllu
python ./src/test.py -s <file>.csv
mv scores.tsv scores_triples.tsv
```

## evaluation
```{bash}
python src/regress.py -tr <scores>.tsv -m <ig_sum or ig_ent> [--plot --all]
```

