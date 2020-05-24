# infogain
using information gain to describe adj order

## source data
[CoNLL 2017 Shared Task - Automatically Annotated Raw Texts and Word Embeddings](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1989)

## pipeline
*1. extract pairs from conllu file*
```{bash}
./tools/wiki/extract_conllu_pairs.sh <file>.conllu
```

*2. extract triples from conllu file*
```{bash}
./tools/wiki/extract_conllu_triples.sh <file>.conllu
```

*3. score triples based on pairs*
```{bash}
python src/partition.py -p <pairs>.csv -t <triples>.csv
```
