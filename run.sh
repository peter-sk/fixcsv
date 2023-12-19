#!/bin/bash
python split.py $(find data/* -type f) && \
python clean.py data_splitted/* && \
python augment.py data_cleaned/* && \
python align.py data_augmented/* && \
python extract.py data_fixed/* && \
python stats.py data_fixed/* && \
wc -l data_extracted/*
