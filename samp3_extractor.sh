filepath="sparky_data.json"
myids=( $(git log --format="%H" $filepath) )
 
for (( i=0,j=1; i < ${#myids[@]}; i++,j++ )) 
    do
        echo $i $j
        name="temp/a$j.txt"
        sha=${myids[$i]}
        git show $sha:$filepath > $name
    done
