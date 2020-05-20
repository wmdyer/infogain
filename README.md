# infogain
using information gain to describe adj order

## pipeline

*1. download data*
* [UD model](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
* [Wikipedia monolingual dump](https://linguatools.org/tools/corpora/wikipedia-monolingual-corpora/)

*2. create text file from Wikipedia dump*
```{bash}
./tools/wiki/xml2txt.pl -nomath -notables <input>.xml <output>.txt
```

*3. create conllu file from text file*
```{bash}
python tools/wiki/make_conllu.py -f <file>.txt -m <model>.udpipe
```

*4. extract pairs from conllu file*
```{bash}
./tools/wiki/extract_conllu_pairs.sh <file>.conllu
```

*5. extract triples from conllu file*
```{bash}
./tools/wiki/extract_conllu_triples.sh <file>.conllu
```

*6. score triples based on pairs*
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
