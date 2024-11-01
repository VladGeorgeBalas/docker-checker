#!/bin/sh

apt-get install python3 python3-pip
python3 -m venv local
source local/bin/activate
pip install GitPython docker
