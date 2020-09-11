fn="100"
fl="2"

lang="`ls | grep wikipedia | cut -d"-" -f1 | head -1`"

if [ "`ls | grep conllu.wiki`" == "" ]
then
    echo -e "\nGENERATE conllu.wiki"
    cat $lang-wikipedia-000.conllu > conllu.wiki
    cat $lang-wikipedia-001.conllu >> conllu.wiki
    #cat $lang-wikipedia-002.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.wiki
    #cat $lang-wikipedia-003.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.wiki
    #cat $lang-wikipedia-004.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.wiki
fi

if [ "`ls | grep conllu.cc`" == "" ]
then
    echo -e "\nGENERATE conllu.cc"
    cat $lang-common_crawl-000.conllu > conllu.cc
    cat $lang-common_crawl-001.conllu >> conllu.cc
    #cat $lang-common_crawl-002.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.cc
    #cat $lang-common_crawl-003.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.cc
    #cat $lang-common_crawl-004.conllu | grep -E "(ADJ)|(NOUN)" >> conllu.cc
fi

if [ "`ls | grep clusters.csv`" == "" ]
then
    echo -e "\nCLUSTER (wiki)"
    ../../tools/cluster.sh conllu.wiki cc.$lang.300.vec 5000 0.1
fi

if [ "`ls | grep nps.tsv`" == "" ]
then
    echo -e "\nGET NPS (wiki)"
    ../../tools/extract_conllu_nps.sh conllu.wiki
fi

if [ "`ls | grep ig.pkl`" == "" ]
then
    echo -e "\nTRAIN (wiki)"
    python3 ../../src/train.py -n nps.tsv -c clusters.csv -fn $fn -fl $fl
fi

if [ "`ls | grep ^pairs.wiki`" == "" ]
then
    echo -e "\nGET PAIRS (wiki)"
    printf "" > pairs
    i="0"
    while [ "`cat pairs | wc -l`" -lt "20000" -a "`ls | grep -w "$lang-wikipedia-00$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_pairs.sh $lang-wikipedia-00$i.conllu
	i="`expr $i + 1`"
	cat pairs.csv >> pairs
    done
    mv pairs pairs.wiki
fi

if [ "`ls | grep ^pairs.cc`" == "" ]
then
    echo -e "\nGET PAIRS (cc)"
    printf "" > pairs
    i="0"
    while [ "`cat pairs | wc -l`" -lt "20000" -a "`ls | grep -w "$lang-common_crawl-00$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_pairs.sh $lang-common_crawl-00$i.conllu
	i="`expr $i + 1`"
	cat pairs.csv >> pairs
    done
    mv pairs pairs.cc
fi

if [ "`ls | grep scores.pairs.wiki`" == "" ]
then
    echo -e "\nTEST PAIRS (wiki)"
    python3 ../../src/test.py -s pairs.wiki
    mv scores.tsv scores.pairs.wiki
    ../../tools/analyze.sh pairs wiki    
fi

if [ "`ls | grep scores.pairs.cc`" == "" ]
then
    echo -e "\nTEST PAIRS (cc)"
    python3 ../../src/test.py -s pairs.cc
    mv scores.tsv scores.pairs.cc
    ../../tools/analyze.sh pairs cc    
fi

echo -e "\nREGRESS PAIRS"
python3 ../../src/regress.py -tr scores.pairs.wiki -te scores.pairs.cc -m ig_sum --plot

if [ "`ls | grep ^triples.wiki`" == "" ]
then
    echo -e "\nGET TRIPLES (wiki)"
    printf "" > triples
    i="0"
    while [ "`cat triples | wc -l`" -lt "20000" -a "`ls | grep -w "$lang-wikipedia-00$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_triples.sh $lang-wikipedia-00$i.conllu
	i="`expr $i + 1`"
	cat triples.csv >> triples
    done
    mv triples triples.wiki
fi

if [ "`ls | grep ^triples.cc`" == "" ]
then
    echo -e "\nGET TRIPLES (cc)"
    printf "" > triples
    i="0"
    while [ "`cat triples | wc -l`" -lt "20000" -a "`ls | grep -w "$lang-common_crawl-00$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_triples.sh $lang-common_crawl-00$i.conllu
	i="`expr $i + 1`"
	cat triples.csv >> triples
    done
    mv triples triples.cc
fi

if [ "`ls | grep scores.triples.wiki`" == "" ]
then
    echo -e "\nTEST TRIPLES (wiki)"
    python3 ../../src/test.py -s triples.wiki
    mv scores.tsv scores.triples.wiki
    ../../tools/analyze.sh triples wiki
fi

if [ "`ls | grep scores.triples.cc`" == "" ]
then
    echo -e "\nTEST TRIPLES (cc)"
    python3 ../../src/test.py -s triples.cc
    mv scores.tsv scores.triples.cc
    ../../tools/analyze.sh triples cc
fi

echo -e "\nREGRESS TRIPLES"
python3 ../../src/regress.py -tr scores.triples.wiki -te scores.triples.cc -m ig_sum --all --plot


