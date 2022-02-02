#!/bin/bash

python3 pqbchord/main.py -p 1001 || python3 pqbchord/secondary.py -p 1002 || python3 pqbchord/secondary.py -p 1003 || python3 pqbchord/secondary.py -p 1004
