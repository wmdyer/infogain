# infogain
using information gain to describe adj order

## pipeline

*1. download conllu file(s)*

[CoNLL 2017 Shared Task - Automatically Annotated Raw Texts and Word Embeddings](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1989)

*2. extract pairs from conllu file*
```{bash}
./tools/wiki/extract_conllu_pairs.sh <file>.conllu
```

*3. extract triples from conllu file*
```{bash}
./tools/wiki/extract_conllu_triples.sh <file>.conllu
```

*4. score triples based on pairs*
```{bash}
python src/partition.py -p <pairs>.csv -t <triples>.csv
```

## evaluation
To compare only *abn* to *ban*, *anb* to *bna*, and *nab* to *nba*:
```{bash}
./tools/accuracy.sh <scores>.csv
```

To compare attested order to all possible orders:
```{bash}
python tools/ranked_accuracy.py -f <scores>.csv
```
Output is a measure of how close the predicted order is to the actual. For example, if *anb* is the actual order, *ban* is the predicted order, and the sorted list of order predictions is [*__ban__, abn, __anb__, bna, nab, nba*], the predicted order is 2 away from the actual order. Because there are 6 possible orders, the accuracy is (6-2)/6 = 0.67.
