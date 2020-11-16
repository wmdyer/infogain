conllu_file="$1"
vec_file="$2"
ak="$3"
nk="$4"
c="$5"

np_file="nps.tsv"

echo $ak > adjs.k
echo $nk > nouns.k

if [ "$c" == "" ]
then
    echo "Usage: ./cluster.sh <conllu_file> <vector_file> <ak> <nk> <c>"
    exit
fi

for t in `echo adjs nouns`
do
    T="`echo $t | tr '[a-z]' '[A-Z]' | tr -d 'S'`"
    echo $T

    if [ "`ls | grep "^$t$"`" == "" ]
    then
	if [ "`ls | grep -w $conllu_file`" != "" -a "`wc -l $conllu_file`" != "0" ]
	then
	    echo "extracting from $conllu_file..."
	    gawk 'BEGIN{FS="\t"}{if($4=="'$T'") print tolower($3) FS tolower($2)}' $conllu_file | grep -vE '(\$)|(\%)|(")' | grep -v "'" | sort | uniq -c | sort -rn | head -100000 | sed -e 's/^[ ]*[0-9]*[ ]*//' | gawk 'BEGIN{FS="\t"}{if($1~"_") print $2 FS $2; else print $0}' > $t
	else
	    echo "extracting from $np_file..."
	    if [ "$T" == "NOUN" ]
	    then
		cat $np_file | cut -f2 | grep -vE '(\$)|(\%)|(")' | grep -v "'" | sort -u | gawk 'BEGIN{FS="\t"}{print tolower($1) FS tolower($1)}' > $t
	    else
		cat $np_file | cut -f3 | tr ',' '\n' | grep -vE '(\$)|(\%)|(")' | grep -v "'" | sort -u | gawk 'BEGIN{FS="\t"}{print tolower($1) FS tolower($1)}' > $t
	    fi
	fi
    fi
    
    if [ "`ls | grep -w $t.norm`" == "" ]
    then
	echo "joining to UD..."
	join -t$'\t' <(cat $t | sort -k1,1) <(cat $t.ud | sort -k1,1) | gawk 'BEGIN{FS="\t"}{print tolower($0)}' > $t.norm
    fi

    if [ "`ls | grep -w $t.forms`" == "" ]
    then
	echo "combining forms ..."
	gawk 'BEGIN{FS="\t";W=""}{if($1!=W) printf "\n" $1 FS $1; if($1!=$2) printf "," $2}{W=$1}' $t.norm > $t.forms
    fi

    k="`cat $t.k`"
    fk="`cat $t.forms | wc -l`"
    if [ "$fk" -lt "$k" ]
    then
	echo "not enough forms ($fk<$k); skipping clustering"
	cat $t.forms | gawk 'BEGIN{FS="\t"}{print $1 "," NR}' > clusters.csv
    else
	if [ "`ls | grep $t.vecs`" == "" ]
	then
	    echo "extracting vectors ..."
	    join <(cat $t.norm | tr '\t' '\n' | sort -u) <(cat $vec_file | sort -k1,1) | gawk 'BEGIN{FS=" "}{if(NF==301) print $0}' > $t.vecs
	fi
	python3 ../../src/cluster.py -v $t.vecs -f $t.forms -k $k -c $c
    fi
    mv clusters.csv $t.cl
done

echo "lemma,cl" > clusters.csv
cat nouns.cl | grep "[0-9]" | gawk 'BEGIN{FS=","}{print $1"/NOUN" FS $2}' | grep -vE '(\$)|(\%)|(")' | grep -v "'" >> clusters.csv
cat adjs.cl | grep "[0-9]" | gawk 'BEGIN{FS=","}{print $1"/ADJ" FS ($2+'$k')}' | grep -vE '(\$)|(\%)|(")' | grep -v "'" >> clusters.csv
