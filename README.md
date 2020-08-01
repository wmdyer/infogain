# infogain
using information gain to describe adj order

## source data
[CoNLL 2017 Shared Task - Automatically Annotated Raw Texts and Word Embeddings](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1989)

or

[Universal Dependencies](https://github.com/UniversalDependencies)

## training
*1. extract NPs from conllu file*
```{bash}
./tools/extract_conllu_nps.sh <file>.conllu
```

*2. cluster*
```{bash}
cat nps.tsv | cut -f2,3 | tr '\t,' '\n' | sort -u > words
join <(cat words | sort -k1,1) <(cat <vectors> | sort -k1,1) > vecs
python ./src/cluster.py -v vecs -w words -k 500 -c 0.25
```

*3. train*
```{bash}
python ./src/train.py -n nps.tsv -c clusters.csv -fn 20 -fl 2
```

## testing

*1. test on AN/NA pairs*
```{bash}
./tools/extract_conllu_pairs.sh <file>.conllu
python ./src/test.py -s pairs.csv
mv scores.temp scores_pairs.csv
```

*2. test on AAN triples*
```{bash}
./tools/extract_conllu_triples.sh <file>.conllu
python ./src/test.py -s triples.csv
mv scores.temp scores_triples.csv
```

## evaluation
```{bash}
python src/regress.py -tr <scores>.csv -m <ig_sum or ig_ent> [--plot --all]
```
