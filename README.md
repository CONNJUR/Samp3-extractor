### Instructions ###

1. run the samp3_extractor.sh shell script in the directory of the samp3 
   analysis data.  This will extract all versions of the JSON dump file
   from the git history

2. run the spextractor/dump2star.py or spextractor/stardiff.py modules,
   depending on what you're trying to do
   
   assuming that 1) you want to do the full diff on a sequence of JSON files,
   2) they are sequentially numbered `a*.txt` in the `temp/` directory,
   and 3) the max index is 38 (with 1 as the newest snapshot, 38 as the first):
   
        python -m spextractor.stardiff temp 38

3. the final result is a single NMR-STAR file using the new data dictionary
   extensions

