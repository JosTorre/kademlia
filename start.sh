#!bin/bash/

count=5
python3 pqbchord/main.py -p 1 &
for ((i=0; i=<count;i++)) 
do
	python3 pqbchord/secondary.py -p i &
done
