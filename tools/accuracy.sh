cat $1 | grep "^abn" | gawk 'BEGIN{FS=","}{print $5+$6 FS $7+$8}' | gawk 'BEGIN{FS=",";P=0;F=0}{if($1<$2) P++; if($1>$2) F++};END{T=P+F; if(T>0) print "abn\t"  P"/"T "\t" P/T; else print "abn\t0/0\t0"}'

cat $1 | grep "^anb" | gawk 'BEGIN{FS=","}{print $5+$11 FS $7+$9}' | gawk 'BEGIN{FS=",";P=0;F=0}{if($1<$2) P++; if($1>$2) F++};END{T=P+F; if(T>0) print "anb\t" P"/"T "\t" P/T; else print "anb\t0/0\t0"}'

cat $1 | grep "^nab" | gawk 'BEGIN{FS=","}{print $9+$10 FS $11+$12}' | gawk 'BEGIN{FS=",";P=0;F=0}{if($1<$2) P++; if($1>$2) F++};END{T=P+F; if(T>0) print "nab\t" P"/"T "\t" P/T; else print "nab\t0/0\t0"}'

