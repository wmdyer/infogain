if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_nps.sh <conllu>"
    exit
fi

printf "" > nps
echo "count\tnoun\tadjs" > nps.tsv


file="$1"
echo $file

# add sentence IDs
printf " sents"
cat $file | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";S=0}{if($1=="1") S++; if($4=="ADJ" || $4=="NOUN") print S FS $0}' > sents

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

# convert pairs to words, then extract NOUN-ADJ pairs, normalize, then combine pairs into NPs
printf " nps1"
join -t$'\t' -1 2 <(join -t$'\t' -1 1 <(cat pairs | sort -k1,1) <(cat words | sort -k1,1) | sort -k2,2) <(cat words | sort -k1,1) | grep -v '\$' | gawk 'BEGIN{FS="\t"}{if(NF==4 && $3 ~ "/NOUN" && $4 ~ "/ADJ") print $0}' > p

printf " nps2"
join -t$'\t' -1 4 <(join -t$'\t' -1 5 <(cat p | tr '/' '\t' | gawk 'BEGIN{FS="\t"}{if(NF==6) print tolower($0)}' | grep -v " " | sort -k5,5) <(cat adjs.ud | sort -k1,1) | sort -k4,4) <(cat nouns.ud | sort -k1,1) | gawk 'BEGIN{FS="\t"}{print $3 FS $4 FS $1"/"toupper($5) FS $2"/"toupper($6)}' > p2

printf " nps3"
cat p2 | sort -k2,2 | gawk 'BEGIN{FS="\t";N=0;A=""}{if(N==$2) printf FS $4; else printf "\n" $3 FS $4}{N=$2;A=$4}' | tr '\t' ',' | grep "." > nps

printf "\n"

# verify each row has >1 cols and normalize
cat nps | gawk 'BEGIN{FS=","}{if(NF>1) print $0}' | tr -d '" ' | sed -e 's/,/\t/' | grep "/NOUN.*/ADJ" | gawk 'BEGIN{FS="\t"}{if(NF==2 && $1!="" && $2!="") print $0}' > nps.tsv

# strip '/POS'
cat nps.tsv | sed -e 's|/[A-Z]*||g' | grep -v '/' > temp; mv temp nps.tsv

# inserts counts
cat nps.tsv | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' ' '\t' > temp; mv temp nps.tsv

# remove hapaxes
#cat nps.tsv | gawk 'BEGIN{FS="\t"}{if($1!="1") print $0}' > nps.nh

# output counts of nps by type
#cat nps.nh | cut -f3 | gawk 'BEGIN{FS=","}{print NF}' | sort | uniq -c | sort -rn | gawk 'BEGIN{FS=" "}{print $0 FS "ADJ"}'

# clean up
rm p
rm p2
rm sents
rm nps
rm words
rm children
rm all_nouns
rm pairs
