if [ "$1" == "" ]
then
    echo "Usage: ./normalize_raw_file.sh <pairs>"
    exit
fi

#if [ "`ls | grep -w wlist`" == "" ]
#then
#    echo "creating word list from $2 ..."
#    cat $2 | cut -d" " -f1 > wlist
#fi


outfile="`echo $1 | sed -e 's/raw_//'`"

echo "counting lines in $1 ..."
f="`echo $1 | sed -e 's/raw_//'`"

#token_count="`cat $1 | wc -l`"

if [ "`echo $1 | grep "triples"`" == "" ]
then

    if [ "1" == "2" ]
    then
	cat $1 | tr -d '"' | tr -d "'" | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' ' ',' | gawk 'BEGIN{FS=","}{if(NF==3) print $0}' > $f    	
	join -t$'\t' -2 2 <(cat words.csv | sort -k1,1) <(cat $f | grep -v "^count," | tr ',' '\t' | sort -k2,2) > a
	join -t$'\t' -2 3 <(cat words.csv | sort -k1,1) <(cat a | sort -k3,3) > b
	echo "count,awf,nwf" > $outfile	
	cat b | gawk 'BEGIN{FS=","}{print $3","$2","$1}' | sort -u > $outfile	
    else
	echo "count,awf,nwf" > $outfile		
	#cat $1 | sort -u | gawk 'BEGIN{FS=","}{if(NF==2) print $0}' | grep "^[abcdefghijklmnoprstuvxyåæéø,]*$" | gawk 'BEGIN{FS=","}{print "1" FS $0}' >> $outfile
	cat $1 | sort -u | gawk 'BEGIN{FS=","}{if(NF==2) print $0}' | gawk 'BEGIN{FS=","}{print "1" FS $0}' >> $outfile	
    fi
    
    token_count="`cat $outfile | wc -l`"    
else
    cat $1 | tr -d '"' | tr -d "'" | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' ' ',' | gawk 'BEGIN{FS=","}{if(NF==4) print $0}' > $f
    echo "joining word list and pairs ..."
    join -t$'\t' -2 2 <(cat wlist | sort -k1,1) <(cat $f | grep -v "^count," | tr ',' '\t' | sort -k2,2) > a
    join -t$'\t' -2 3 <(cat wlist | sort -k1,1) <(cat a | sort -k3,3) > b
    join -t$'\t' -2 4 <(cat wlist | sort -k1,1) <(cat b | sort -k4,4) > c

    echo "count,awf1,awf2,nwf" > $outfile
    cat c | gawk 'BEGIN{FS="\t"}{print $4","$1","$2","$3}' | sort -u >> $outfile

    f="aa_pairs.csv"

    cat $1 | cut -d"," -f2,3 | tr -d '"' | tr -d "'" | sort | uniq -c | sed -e 's/^[ ]*//' | tr ' ' ',' | gawk 'BEGIN{FS=","}{if(NF==3) print $0}' > $f

    join -t$'\t' -2 2 <(cat wlist | sort -k1,1) <(cat $f | grep -v "^count," | tr ',' '\t' | sort -k2,2) > a
    join -t$'\t' -2 3 <(cat wlist | sort -k1,1) <(cat a | sort -k3,3) > b    

    echo "count,awf1,awf2" > $f
    cat b | gawk 'BEGIN{FS="\t"}{print $3","$2","$1}' | sort -u >> $f
fi

echo "tokens: $token_count"
