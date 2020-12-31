test="true"
threshold="50000"

lang="`pwd | rev | cut -d"/" -f1 | rev`"

#if [ "`ls | grep clusters.csv`" == "" ]
#then
#    echo -e "\nCLUSTER (wiki)"
#    ../../tools/cluster.sh conllu.wiki cc.$lang.300.vec $ak $nk 0.1
#fi

if [ "`ls | grep nps.tsv`" == "" ]
then
    echo -e "\nGET NPS (wiki)"
    ../../tools/extract_conllu_nps.sh conllu.wiki
fi

if [ "`ls | grep ig.pkl`" == "" ]
then
    echo -e "\nBUILD FEAT VECS (wiki)"
    python3 ../../src/build_feature_vecs.py -n <(cat nps.tsv | sort -rnk1,1 | head -100000)
fi

if [ "`ls | grep ^triples.wiki`" == "" ]
then
    echo -e "\nGET TRIPLES (wiki)"
    printf "" > triples
    i="0"
    while [ "`cat triples | wc -l`" -lt "$threshold" -a "`ls | grep -w "$lang-wikipedia-00$i.conllu"`" != "" ]
    do
	echo "triples"
	../../tools/extract_conllu_triples.sh $lang-wikipedia-00$i.conllu
	i="`expr $i + 1`"
	cat triples.csv >> triples
    done
    
    cat triples | shuf -n $threshold triples > triples.wiki
fi

if [ "`ls | grep ^triples.cc`" == "" -a "$test" == "true" ]
then
    echo -e "\nGET TRIPLES (cc)"
    printf "" > triples
    i="0"
    while [ "`cat triples | wc -l`" -lt "$threshold" -a "`ls | grep  -w "$lang-common_crawl-00$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_triples.sh $lang-common_crawl-00$i.conllu
	i="`expr $i + 1`"
	cat triples.csv >> triples
    done
    while [ "`cat triples | wc -l`" -lt "$threshold" -a "`ls | grep  -w "$lang-common_crawl-0$i.conllu"`" != "" ]
    do
	../../tools/extract_conllu_triples.sh $lang-common_crawl-0$i.conllu
	i="`expr $i + 1`"
	cat triples.csv >> triples
    done    
    cat triples | shuf -n $threshold > triples.cc
fi

#for t in `echo wiki cc`
#do
#    if [ "`ls | grep -w "triples.$t.norm"`" == "" ]
#    then
#	echo -e "\nNORMALIZE TRIPLES ($t)"
#	../../tools/normalize.sh triples.$t
#    fi
#done

for t in `echo wiki cc`
do
    if [ "`ls | grep scores.$t`" == "" ]
    then
	echo -e "\nTEST TRIPLES ($t)"
	python3 ../../src/partition.py -s triples.$t
	mv scores.tsv scores.$t
    fi
done

if [ "$1" == "" ]
then
    m="1st_a uc_pos uc_neg"
else
    m="$1"
fi

printf "" > report.txt

for t in `echo $m`
do
    echo -e "\nREGRESS TRIPLES ($t)"
    python3 ../../src/regress.py -tr scores.wiki -te scores.cc -m ig_$t | tee -a report.txt
done

