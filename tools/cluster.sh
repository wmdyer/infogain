conllu_file="$1"
vec_file="$2"
k="$3"
c="$4"

if [ "$c" == "" ]
then
    echo "Usage: ./cluster.sh <conllu_file> <vector_file> <k> <c>"
    exit
fi

if [ "`ls | grep -w forms`" == "" ]
then
    echo "extracting ADJs and NOUNs ..."
    cat $conllu_file | grep "^[0-9]" | gawk 'BEGIN{FS="\t"}{if($4=="ADJ" || $4=="NOUN") print $3 FS $2}' | grep -vE '(\$)|(\%)|(")' | grep -v "'" | sort -u > words

    echo "extracting vectors ..."
    join <(cat words | tr '\t' '\n' | sort -u) <(cat $vec_file | sort -k1,1) | gawk 'BEGIN{FS=" "}{if(NF==301) print $0}' > vecs

    echo "combining forms ..."
    cat words | gawk 'BEGIN{FS="\t";W=""}{if($1!=W) printf "\n" $1 FS $1; if($1!=$2) printf "," $2}{W=$1}' > forms
fi

python3 ../../src/cluster.py -v vecs -f forms -k $k -c $c
