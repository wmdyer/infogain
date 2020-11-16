code="`pwd | rev | cut -d"/" -f1 | rev | sed -e 's/_cl//' | tr -d '[0-9]'`"
lang="`gawk 'BEGIN{FS="\t"}{if($1=="'$code'") print $2}' ../langcodes.tsv`"

if [ "$lang" == "" ]
then
    echo "ERROR: language for code '$code' not found"
    exit
fi

if [ "`ls | grep adjs.ud`" == "" -o "`ls | grep nouns.ud`" == "" ]
then
    echo "copying UD $lang files ..."
    cp ../ud/UD_$lang-*/*.conllu .

    for t in `echo adj noun`
    do
	echo "extracting $t"s" ..."
	T="`echo $t | tr '[a-z]' '[A-Z]'`"
	gawk 'BEGIN{FS="\t"}{if($4=="'$T'") print tolower($3)}' *-ud-*.conllu | sort -u > $t"s.ud"
    done
fi

if [ "$1" == "" ]
then
    exit
fi

if [ "`cat $1 | head -1 | gawk 'BEGIN{FS=","}{print NF}'`" == "3" ]
then
    printf "" > $1.norm
    
    #NAA
    join -t$'\t' -1 3 <(join -t$'\t' -1 5 <(join -t$'\t' -1 3 <(cat $1 | grep "NOUN.*ADJ.*ADJ.*" | tr '/,' '\t' | grep -v " " | gawk 'BEGIN{FS="\t"}{if(NF==6) print tolower($0)}' | sort -k3,3) <(cat adjs.ud | sort -k1,1) | sort -k5,5) <(cat adjs.ud | sort -k1,1) | sort -k3,3) <(cat nouns.ud | sort -k1,1) | gawk 'BEGIN{FS="\t"}{print $1"/"toupper($4) "," $3"/"toupper($6) "," $2"/"toupper($5)}' > $1.norm

    #ANA
    join -t$'\t' -1 5 <(join -t$'\t' -1 2 <(join -t$'\t' -1 3 <(cat $1 | grep "ADJ.*NOUN.*ADJ.*" | tr '/,' '\t' | grep -v " " | gawk 'BEGIN{FS="\t"}{if(NF==6) print tolower($0)}' | sort -k3,3) <(cat nouns.ud | sort -k1,1) | sort -k2,2) <(cat adjs.ud | sort -k2,2) | sort -k5,5) <(cat adjs.ud | sort -k1,1) | gawk 'BEGIN{FS="\t"}{print $2"/"toupper($4) "," $3"/"toupper($5) "," $1"/"toupper($6)}' >> $1.norm

    #AAN
    join -t$'\t' -1 5 <(join -t$'\t' -1 3 <(join -t$'\t' <(cat $1 | grep "ADJ.*ADJ.*NOUN" | tr '/,' '\t' | grep -v " " | gawk 'BEGIN{FS="\t"}{if(NF==6) print tolower($0)}' | sort -k1,1) <(cat adjs.ud | sort -k1,1) | sort -k3,3) <(cat adjs.ud | sort -k1,1) | sort -k5,5) <(cat nouns.ud | sort -k1,1) | gawk 'BEGIN{FS="\t"}{print $3"/ADJ," $2"/ADJ," $1"/NOUN"}' >> $1.norm

fi
