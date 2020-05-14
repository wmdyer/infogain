(for pg in 1 2 3; do wget "https://api.github.com/orgs/UniversalDependencies/repos?page=$pg&per_page=100" -O - ; done ) | grep git_url | grep -Po 'git://.*?(?=")' > all_repos.txt

for repo in `cat all_repos.txt | grep UD_`
do
    lang="`echo $repo | cut -d"/" -f5 | cut -d"." -f1`"
    if [ "`ls | grep -w $lang`" == "" ]
    then
	git clone $repo
    else
	cd $lang
	git fetch
	cd ..
    fi
done

rm all_repos.txt
