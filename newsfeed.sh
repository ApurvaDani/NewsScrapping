#!/bin/sh

output_dir="./newsoutput"
source_dir="./news_source.txt"
total_symbols=4

python scrapenews.py --output_dir $output_dir --source_path $source_dir --total_symbols $total_symbols