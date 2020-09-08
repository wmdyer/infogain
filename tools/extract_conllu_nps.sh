if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_nps.csv <conllu files>"
    exit
fi

printf "" > nps
echo "count\tnoun\tadjs" > nps.tsv


# if $1 doesn't exist, use $1 to grep through files; else use $@
if [ "`ls | grep -w "$1"`" == "" ]
then
    files="`ls | grep $1`"
else
    files="$@"
fi

for file in $files
do
    echo $file

    # add sentence IDs
    printf " sents"
    cat $file | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";S=0}{if($1=="1") S++; print S FS $0}' > sents

    # extract all lemmas and key them to sentence:index
    printf " words"
    cat sents | grep -v '%' | gawk 'BEGIN{FS="\t"}{if($4!="_") print $1":"$2 FS $4"/"$5; else print $1":"$2 FS $3"/"$5}' > words

    # extract all children
    printf " children"
    cat sents | gawk 'BEGIN{FS="\t"}{print $1":"$2 FS $1":"$8}' > children

    # extract all nouns
    printf " all_nouns"
    cat sents | gawk 'BEGIN{FS="\t"}{if($5=="NOUN") print $1":"$2}' > all_nouns

    # join all_nouns and children
    printf " pairs"
    join -t$'\t' -1 2 -a2 <(cat children | sort -k2,2) <(cat all_nouns | sort -k1,1) | gawk 'BEGIN{FS="\t"}{if(NF==2) print $0}' > pairs

    # convert pairs to words, then extract NOUN-ADJ pairs, then NPs
    printf " nps"
    join -t$'\t' -1 2 <(join -t$'\t' -1 1 <(cat pairs | sort -k1,1) <(cat words | sort -k1,1) | sort -k2,2) <(cat words | sort -k1,1) | grep -v '\$' | gawk 'BEGIN{FS="\t"}{if(NF==4) print $0}' | gawk 'BEGIN{FS="\t"}{if($4 ~ "/ADJ") print $0}' | gawk 'BEGIN{FS="\t";N=0}{if(N!=$2) printf "\n" $3; printf FS $4}{N=$2}' | tr '\t' ',' | grep "." >> nps
    
    printf "\n"
done

# verify each row has >1 cols and normalize
cat nps | gawk 'BEGIN{FS=","}{if(NF>1) print $0}' | tr -d '" ' | sed -e 's/,/\t/' | grep "/NOUN.*/ADJ" | gawk 'BEGIN{FS="\t"}{if(NF==2) print $0}' > nps.tsv

# strip '/POS'
cat nps.tsv | sed -e 's|/[A-Z]*||g' | grep -v '/' > temp; mv temp nps.tsv

# inserts counts
cat nps.tsv | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' ' '\t' > temp; mv temp nps.tsv

# remove hapaxes
cat nps.tsv | gawk 'BEGIN{FS="\t"}{if($1!="1") print $0}' > nps.nh

# output counts of nps by type
cat nps.nh | cut -f3 | gawk 'BEGIN{FS=","}{print NF}' | sort | uniq -c | sort -rn | gawk 'BEGIN{FS=" "}{print $0 FS "ADJ"}'

# clean up
rm sents
rm nps
rm words
rm children
rm all_nouns
rm pairs
