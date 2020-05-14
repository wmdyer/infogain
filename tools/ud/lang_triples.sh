for lang in `ls | grep UD_ | sed -e 's/UD_//' | cut -d"-" -f1 | sort -u`
do
    repos="`ls | grep "UD_"$lang"\-" | tr '\n' ' '`"
    ../git/tools/ud/extract_ud_triples.sh $repos
    mv triples.csv $lang"_triples.csv"
done
