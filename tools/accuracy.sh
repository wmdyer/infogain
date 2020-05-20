cat $1 | grep "^abn" | gawk 'BEGIN{FS=",";P=0;F=0}{if($5<$6) P++; if($5>$6) F++};END{T=P+F; if(T>0) print "abn\t"  P"/"T "\t" P/T; else print "abn\t0/0\t0"}'

cat $1 | grep "^anb" | gawk 'BEGIN{FS=",";P=0;F=0}{if($7<$8) P++; if($7>$8) F++};END{T=P+F; if(T>0) print "anb\t" P"/"T "\t" P/T; else print "anb\t0/0\t0"}'

cat $1 | grep "^nab" | gawk 'BEGIN{FS=",";P=0;F=0}{if($9<$10) P++; if($9>$10) F++};END{T=P+F; if(T>0) print "nab\t" P"/"T "\t" P/T; else print "nab\t0/0\t0"}'

