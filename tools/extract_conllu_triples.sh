if [ "$1" == "" ]
then
    echo "Usage: ./extract_conllu_triples.csv <conllu files>"
    exit
fi

printf "" > triples.csv

file="$1"
echo $file

# add sentence IDs
printf " sents"
cat $file | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";S=0}{if($1=="1") S++; print S FS $0}' > sents

# extract all lemmas and key them to sentence:index
printf " words"
cat sents | gawk 'BEGIN{FS="\t"}{if($4!="_") print $1":"$2 FS $4"/"$5; else print $1":"$2 FS $3"/"$5}' > words

# extract all nouns
printf " all_nouns"
cat sents | gawk 'BEGIN{FS="\t"}{if($5=="NOUN") print $1":"$2 FS $1":"$8}' > all_nouns

# extract all adjectives
printf " all_adjs"
cat sents | gawk 'BEGIN{FS="\t"}{if($5=="ADJ" && $9=="amod") print $1":"$2 FS $1":"$8}' > all_adjs

# extract all dependent-head pairs
printf " children"
cat sents | gawk 'BEGIN{FS="\t"}{print $1":"$2 FS $1":"$8}' > children

# join children and all adjs -- if resulting line has only two fields, it's a childless adj
printf " childless"
join -t$'\t' -1 2 -a2 <(cat children | sort -k2,2) <(cat all_adjs | sort -k1,1) | gawk 'BEGIN{FS="\t"}{if(NF==2) print $0}' > childless

# get nouns with only two dependents
printf " noun_2_deps"
join -t$'\t' -1 2 <(cat children | sort -k2,2) <(cat all_nouns | cut -f1 | sort -k1,1) | sort -k1,1 | gawk 'BEGIN{FS="\t";S=""}{if(S!=$1) printf "\n" $1; printf "\t" $2}{S=$1};END{printf "\n"}' | gawk 'BEGIN{FS="\t"}{if(NF==3) print $1}' > nouns_2_deps

# modify childless so its head nouns are only nouns with 2 deps
printf " childless"
join -t$'\t' -2 2 <(cat nouns_2_deps | sort -k1,1) <(cat childless | sort -k2,2) | gawk 'BEGIN{FS="\t"}{print $2 FS $1}' > temp; mv temp childless

# get postnominal adjs
printf " ids1"
cat childless | gawk 'BEGIN{FS="\t"}{print $2 FS $1}' | sort -k1,1 | gawk 'BEGIN{FS="\t";H=""}{if($1!=H){printf "\n"$1}; printf FS $2}{H=$1}' | gawk 'BEGIN{FS="\t"}{if(NF==3) print $0}' > ids

# get prenominal adjs
printf " ids2"
cat childless | gawk 'BEGIN{FS="\t"}{print $1 FS $2}' | sort -k1,1 | gawk 'BEGIN{FS="\t";H=""}{if($2!=H){printf "\n"$2}; printf FS $1}{H=$2}' | gawk 'BEGIN{FS="\t"}{if(NF==3) print $0}' >> ids

# join adjs to their head noun and split into triples
printf " ids3"
cat ids | sort -u | tr '\t' '\n' | tr ':' '\t' | sort -k1,1 -nk2,2 | tr '\t' ':' | gawk 'BEGIN{FS=":";S=""}{if(S!=$1) printf "\n"; printf "\t" $1":"$2}{S=$1};END{printf "\n"}' | sed -e 's/^\t//' | sed -e 's/\([0-9:]*\)\t\([0-9:]*\)\t\([0-9:]*\)\t/\1\t\2\t\3\n/g' | grep ":" > temp; mv temp ids

# make sure word indices are consecutive
printf " ids4"
cat ids | tr ':' '\t' | gawk 'BEGIN{FS="\t"}{if($2+1 == $4 && $4+1==$6) print $1":"$2 FS $3":"$4 FS $5":"$6}' > temp; mv temp ids

# convert IDs to words and select triples of interest
printf " triples1"
join -t$'\t' -1 3 <(join -t$'\t' -1 2 <(join -t$'\t' <(cat ids | sort -k1,1) <(cat words | sort -k1,1) | sort -k2,2) <(cat words | sort -k1,1) | sort -k3,3) <(cat words | sort -k1,1) | cut -f4,5,6 | tr '\t' ',' | grep -E "(NOUN.*ADJ.*ADJ)|(ADJ.*NOUN.*ADJ)|(ADJ.*ADJ.*NOUN)" >> triples.csv

printf "\n"

# verify each row has 3 cols and normalize
echo "validate"
cat triples.csv | gawk 'BEGIN{FS=","}{if(NF==3) print $0}' | tr -d '"'  > temp; mv temp triples.csv
    
# output counts of triples by type
cat triples.csv | grep "NOUN.*ADJ.*ADJ" | wc -l | gawk 'BEGIN{FS="\t"}{print "NAA: " $1}'
cat triples.csv | grep "ADJ.*NOUN.*ADJ" | wc -l | gawk 'BEGIN{FS="\t"}{print "ANA: " $1}'
cat triples.csv | grep "ADJ.*ADJ.*NOUN" | wc -l | gawk 'BEGIN{FS="\t"}{print "AAN: " $1}'

# clean up
rm sents
rm all_adjs
rm children
rm childless
rm ids
rm nouns_2_deps
rm words
