# infogain
using information gain to describe adj order

## pipeline

1. download data
* [UD model](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
* [Wikipedia monolingual dump](https://linguatools.org/tools/corpora/wikipedia-monolingual-corpora/)

1. create text file from Wikipedia dump
`$ tools/wiki/xml2txt.pl <input xml file> <output text file>`

1. create conllu file from text file
`$ tools/wiki/make_conllu.py <text file>`

1. extract pairs from conllu file
`$ tools/wiki/extract_conllu_pairs.sh <conllu file>`

1. extract triples from conllu file
`$ tools/wiki/extract_conllu_triples.sh <conllu file>`

1. score triples based on pairs
`$ src/partition.py -p <pairs file> -t <triples file>`
