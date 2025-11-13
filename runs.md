poetry run python evaluation.py \
    /home/benedikt-baumgartner/Dokumente/GitHub/PII_Detection/Data/texts/echr_dev.json \
    /home/benedikt-baumgartner/Schreibtisch/logs/log/final.json
    
time poetry run python src/cli/main.py --input_path /app/Data/texts/echr_test.json --output_path /app/Output --n_text 30 --refine 0

real	294m1.399s
user	2m8.098s
sys	0m6.437s


==> Token-level recall on all identifiers: 0.875
==> Token-level recall on all identifiers, factored by type:
	DATETIME:0.926
	CODE:0.992
	PERSON:0.951
	LOC:0.879
	ORG:0.685
	QUANTITY:0.768
	DEM:0.799
	MISC:0.384
==> Mention-level recall on all identifiers: 0.843
==> Entity-level recall on direct identifiers: 0.961
==> Entity-level recall on quasi identifiers: 0.855
==> Uniform token-level precision on all identifiers: 0.512
==> Uniform mention-level precision on all identifiers: 0.556




-- Mit new prompt
real	499m5.961s
user	2m48.188s
sys	0m9.733s
