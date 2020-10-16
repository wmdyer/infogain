#seq="$1"
#corpus="$2"

cat triples.wiki > t
cat triples.cc >> t
cat scores.triples.wiki > s
cat scores.triples.cc >> s

start="`cat t | wc -l`"

echo -e "$triples\t$start" > a
cat s | grep "[0-9]" | gawk 'BEGIN{FS="\t";S=0}{S+=$4};END{print "scored" FS S FS S/'$start'}' >> a

cat s | grep "[0-9]" | sort -k1,1 -k3,3 | cut -f1,4,5 | gawk 'BEGIN{FS="\t";K=""}{if(K!=$1) printf "\n"; printf FS $2FS $3};{K=$1}' | sed -e 's/^\t//' > b

cat b | gawk 'BEGIN{FS="\t";S=0;AAN=0;ANA=0;NAA=0}{if(($1!=0 || $3!=0) && ($2!=$4)) {S+=($1+$3); AAN+=($1+$3)}; if (($5!=0 || $7!=0) && ($6!=$8)){S+=($5+$7); ANA+=($5+$7)}; if (($9!=0 || $11!=0) && ($10!=$12)) {S+=($9+$11); NAA+=($9+$11)}};END{print "analyzed" FS S FS S/'$start' "\nAAN" FS AAN FS AAN/S "\nANA" FS ANA FS ANA/S "\nNAA" FS NAA FS NAA/S}' >> a

#for template in `echo AAN ANA NAA`
#do
#    cat b | grep -w $template | gawk 'BEGIN{FS="\t";S=0}{if(($1!=0 || $3!=0) && ($2!=$4)) S+=($1+$3); if (($5!=0 || $7!=0) && ($6!=$8)) S+=($5+$7); if (($9!=0 || $11!=0) && ($10!=$12)) S+=($9+$11)};END{print "'$template'" FS S}' >> a
#done


#cat scores.$seq.$corpus | cut -f1,4 | sort -u | sed -e 's|/[A-Za-z]*||g' | tr ',' '\t' | gawk 'BEGIN{FS="\t";S=0;T=0}{if(NF==4){if($1==$2 || $2==$3 || $1==$3) S+=$4; T+=$4} else{if($1==$2) S+=$3; T+=$3}};END{print "same_clusters" FS S "/" T FS S/T}' >> a
#cat $clust | cut -d"," -f2 | grep "[0-9]" | sort | uniq -c | sed -e 's/^[ ]*//' | cut -d" " -f1 | sort | uniq -c | sed -e 's/^[ ]*//' | gawk 'BEGIN{FS=" ";S=0;T=0}{T+=$1; if($2=="1") S+=$1};END{print "singleton_clusters\t" S"/"T "\t" S/T}' >> a

echo ""
cat a | column -t
