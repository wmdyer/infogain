if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_pairs.sh <conllu file>"
    exit
fi

printf "count,awf,nwf\n" > pairs.csv

file="$1"

# get instances of wordforms that are ADJ/amod or NOUN, keyed as sentence:index
cat $file | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";C=0;W=""}{if($1=="1") C+=1; if(($2!="_") && (($4=="ADJ" && $8=="amod") || ($4=="NOUN"))) print C":"$1 FS $2"/"$4 FS C":"$7}' > a

# join ADJs and NOUNs, normalize, and count
join -2 3 -t$'\t' <(cat a | sort -k1,1) <(cat a | sort -k3,3) | gawk 'BEGIN{FS="\t"}{print $5 FS $2}' | grep "ADJ.*NOUN" | tr '[A-Z]' '[a-z]' | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' \t' ',' | sed -e 's|/adj||' | sed -e 's|/noun||' | gawk 'BEGIN{FS=","}{if($4=="") print $0}' >> pairs.csv

# verify each row has 3 cols
cat pairs.csv | gawk 'BEGIN{FS=","}{if(NF==3) print $0}' > temp; mv temp pairs.csv

# clean up
rm a
