#!/bin/bash
eval "$(/root/miniconda/bin/conda shell.bash hook)"
conda activate brave
cd /root/brave
python brave.py