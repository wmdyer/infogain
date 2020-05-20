# infogain
using information gain to describe adj order

## pipeline

*1. download data*
* [UD model](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
* [Wikipedia monolingual dump](https://linguatools.org/tools/corpora/wikipedia-monolingual-corpora/)

*2. create text file from Wikipedia dump*
  ```{bash}
  tools/wiki/xml2txt.pl -nomath -notables <input>.xml <output>.txt
  ```

*3. create conllu file from text file*
```{bash}
tools/wiki/make_conllu.py <file>.txt
```

*4. extract pairs from conllu file*
```{bash}
tools/wiki/extract_conllu_pairs.sh <file>.conllu
```

*5. extract triples from conllu file*
```{bash}
tools/wiki/extract_conllu_triples.sh <file>.conllu
```

*6. score triples based on pairs*
```{bash}
python src/partition.py -p <pairs>.csv -t <triples>.csv
```

## evaluation
To compare only *abn/ban*, *anb/bna*, and *nab/nba*:
```{bash}
tools/accuracy.sh <scores>.csv
```

To compare attested order to all possible orders:
```{bash}
python tools/ranked_accuracy.py -f <scores>.csv
```
