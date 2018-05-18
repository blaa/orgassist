#!/bin/bash

ENV=~/orgsec_ENV
python3 -m venv $ENV
source $ENV/bin/activate

pip3 install wheel
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
