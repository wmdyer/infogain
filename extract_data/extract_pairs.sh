printf "" > a

for dir in "$@"
do
    echo $dir
    for file in `ls $dir | grep conllu`
    do
	echo "  $file"
	cat $dir/$file | grep "^[0-9][0-9]*"$'\t' | gawk 'BEGIN{FS="\t";C=0}{if($1=="1") C+=1; print C":"$1 FS $2"/"$4 FS C":"$7}' | grep -E "(ADJ)|(NOUN)" >> a
    done
done

join -2 3 -t$'\t' <(cat a | sort -k1,1) <(cat a | sort -k3,3) | gawk 'BEGIN{FS="\t"}{print $5 FS $2}' | grep "ADJ.*NOUN" | sed -e 's|/[A-Z]*||g' | tr '[A-Z]' '[a-z]' | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' \t' ',' > pairs.csv
