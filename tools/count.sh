cc="`../../tools/analyze.sh triples cc | grep analyzed | tr -s ' ' | cut -d" " -f2`"
wiki="`../../tools/analyze.sh triples wiki | grep analyzed | tr -s ' ' | cut -d" " -f2`"
echo "$cc+$wiki" | bc -l
