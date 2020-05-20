# infogain
using information gain to describe adj order

## pipeline

*1. download data*
* [UD model](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
* [Wikipedia monolingual dump](https://linguatools.org/tools/corpora/wikipedia-monolingual-corpora/)

*2. create text file from Wikipedia dump*
  ```{bash}
  tools/wiki/xml2txt.pl -nomath -notables <input xml file> <output text file>
  ```

*3. create conllu file from text file*
```{bash}
tools/wiki/make_conllu.py <text file>
```

*4. extract pairs from conllu file*
```{bash}
tools/wiki/extract_conllu_pairs.sh <conllu file>
```

*5. extract triples from conllu file*
```{bash}
tools/wiki/extract_conllu_triples.sh <conllu file>
```

*6. score triples based on pairs*
```{bash}
src/partition.py -p <pairs file> -t <triples file>
```

## evaluation
```{bash}
tools/accuracy.sh scores.csv
```
