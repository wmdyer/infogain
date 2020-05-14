for lang in `ls | grep UD_ | sed -e 's/UD_//' | cut -d"-" -f1 | sort -u`
do
    repos="`ls | grep "UD_" | grep $lang | tr '\n' ' '`"
    ../tools/extract_pairs.sh $repos
    mv pairs.csv $lang"_pairs.csv"
done
