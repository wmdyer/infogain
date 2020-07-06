if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_pairs.sh <conllu files or language>"
    exit
fi

printf "" > a
printf "count,awf,nwf\n" > pairs.csv

# if $1 doesn't exist, use $1 to grep through files; else use $@
if [ "`ls | grep "$1"`" != "" ]
then
    files="$1"
    if [ "$2" != "" ]
    then
	files="$@"
    fi
else
    files=""
    for dir in `ls ../../ud | grep "UD_$1-"`
    do
	for file in `ls ../../ud/$dir/ | grep conllu`
	do
	    files=$files" "
	    files=$files"../../ud/$dir/$file"
	done
    done
fi

for file in $files
do
    echo $file
    # get instances of wordforms that are ADJ/amod or NOUN, keyed as sentence:index
    cat $file | tr -d ': "/_\*̥\$+\.\-' | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";C=0;W=""}{if($1=="1") C+=1; W=$2; if(($4=="ADJ" && $8=="amod") || ($4=="NOUN")) print C":"$1 FS W"/"$4 FS C":"$7}' >> a
done

# join ADJs and NOUNs, normalize, and count
printf "join"
join -2 3 -t$'\t' <(cat a | sort -k1,1) <(cat a | sort -k3,3) | gawk 'BEGIN{FS="\t"}{print $5 FS $2}' | grep "ADJ.*NOUN" | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' \t' ',' | sed -e 's|/ADJ||' | sed -e 's|/NOUN||' | gawk 'BEGIN{FS=","}{if($4=="") print $0}' >> pairs.csv

# verify each row has 3 cols
printf " validate"
cat pairs.csv | gawk 'BEGIN{FS=","}{if(NF==3 && $1!="" && $2!="" && $3!="") print $0}' > temp; mv temp pairs.csv

printf "\n"
cat pairs.csv | wc -l

# remove hapaxes
cat pairs.csv | grep -v "^1," > pairs_no_hapax.csv
cat pairs_no_hapax.csv | wc -l

# clean up
rm a
