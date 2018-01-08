#!/bin/bash

declare -i cnt=0
while [ $cnt -lt 10 ]
do
python client.py
cnt=$cnt+1
done
