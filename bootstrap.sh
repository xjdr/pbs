#!/bin/bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv virtualenv pbs
pyenv activate pbs
pip install -r requirements.txt


