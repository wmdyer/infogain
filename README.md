# infogain
using information gain to describe adj order

## source data
[CoNLL 2017 Shared Task - Automatically Annotated Raw Texts and Word Embeddings](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1989)

or

[Universal Dependencies](https://github.com/UniversalDependencies)

## pipeline
*1. extract semantic pairs from conllu file*
```{bash}
./tools/wiki/extract_conllu_pairs.sh <file>.conllu
```

*2. extract syntactic sequences from conllu file*
```{bash}
./tools/wiki/extract_conllu_syntactic_pairs.sh <file>.conllu
```
or

```{bash}
./tools/wiki/extract_conllu_triples.sh <file>.conllu
```

*3. score sequences based on pairs*
```{bash}
python src/partition.py -p <pairs>.csv -s <sequences>.csv
```

## evaluation
```{bash}
python src/regress.py -tr <scores>.csv [--plot --all]
```
