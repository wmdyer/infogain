for t in `echo wiki cc`
do
    if [ "`ls | grep scores.ablat.$t`" == "" ]
    then
	echo -e "\nTEST TRIPLES ($t)"
	python3 ../../src/ablate.py -s triples.$t
	mv scores.tsv scores.ablat.$t
    fi
done

#../../tools/analyze.sh

if [ "$1" == "" ]
then
    m="sum uc_pos c_pos uc_neg c_neg"
else
    m="$1"
fi

for t in `echo $m`
do
    echo -e "\nREGRESS TRIPLES ($t)"
    python3 ../../src/regress.py -tr scores.ablat.wiki -te scores.ablat.cc -m ig_$t
done



