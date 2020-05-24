if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_pairs.sh <conllu files>"
    exit
fi

printf "" > a
printf "count,awf,nwf\n" > pairs.csv

for file in "$@"
do
    echo $file
    # get instances of lemmas that are ADJ/amod or NOUN, keyed as sentence:index
    cat $file | tr -d '"/' | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";C=0;W=""}{if($1=="1") C+=1; if(($2!="_") && (($4=="ADJ" && $8=="amod") || ($4=="NOUN"))) print C":"$1 FS $3"/"$4 FS C":"$7}' >> a
done

# join ADJs and NOUNs, normalize, and count
echo "join"
join -2 3 -t$'\t' <(cat a | sort -k1,1) <(cat a | sort -k3,3) | gawk 'BEGIN{FS="\t"}{print $5 FS $2}' | grep "ADJ.*NOUN" | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' \t' ',' | sed -e 's|/ADJ||' | sed -e 's|/NOUN||' | gawk 'BEGIN{FS=","}{if($4=="") print $0}' >> pairs.csv

# verify each row has 3 cols
echo "validate"
cat pairs.csv | gawk 'BEGIN{FS=","}{if(NF==3) print $0}' > temp; mv temp pairs.csv

# clean up
rm a
