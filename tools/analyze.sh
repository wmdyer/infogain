seq="$1"
corpus="$2"

start="`cat $seq.$corpus | wc -l`"

echo -e "$seq.$corpus\t$start" > a
cat scores.$seq.$corpus | grep "[0-9]" | gawk 'BEGIN{FS="\t";S=0}{S+=$4};END{print "scored" FS S FS S/'$start'}' >> a
cat scores.$seq.$corpus | grep "[0-9]" | sort -k1,1 -k3,3 | cut -f1,4,5 | gawk 'BEGIN{FS="\t";K=""}{if(K!=$1) printf "\n"; printf FS $2 FS $3}{K=$1}' | sed -e 's/^\t//' | gawk 'BEGIN{FS="\t";S=0}{if(($1!=0 || $3!=0) && ($2!=$4)) S+=($1+$3); if (($5!=0 || $7!=0) && ($6!=$8)) S+=($5+$7); if (($9!=0 || $11!=0) && ($10!=$12)) S+=($9+$11)};END{print "analyzed" FS S FS S/'$start'}' >> a
cat scores.$seq.$corpus | cut -f1,4 | sort -u | sed -e 's|/[A-Za-z]*||g' | tr ',' '\t' | gawk 'BEGIN{FS="\t";S=0;T=0}{if(NF==4){if($1==$2 || $2==$3 || $1==$3) S+=$4; T+=$4} else{if($1==$2) S+=$3; T+=$3}};END{print "same_clusters" FS S "/" T FS S/T}' >> a
#cat $clust | cut -d"," -f2 | grep "[0-9]" | sort | uniq -c | sed -e 's/^[ ]*//' | cut -d" " -f1 | sort | uniq -c | sed -e 's/^[ ]*//' | gawk 'BEGIN{FS=" ";S=0;T=0}{T+=$1; if($2=="1") S+=$1};END{print "singleton_clusters\t" S"/"T "\t" S/T}' >> a

echo ""
cat a | column -t
