myids=( $(git rev-list --objects master -- sparky_data.json | grep sparky_data | perl -e 'for (<>) { print substr($_, 0, 40) . "\n"; }') )

for (( i=0,j=1; i < ${#myids[@]}; i++,j++ )) 
    do
        echo $i $j
        name="a$j.txt"
        git cat-file -p ${myids[$i]} > $name
    done
