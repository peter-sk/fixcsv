#!/bin/bash
mkdir -v data_splitted data_cleaned data_augmented data_fixed data_extracted data_joined
python split.py $(find data/* -type f) && \
python clean.py data_splitted/* && \
python augment.py data_cleaned/* && \
python align.py data_augmented/* && \
python extract.py data_fixed/* && \
python stats.py data_fixed/* && \
python join.py data_extracted/* && \
wc -l data_extracted/*
wc -l data_joined/*