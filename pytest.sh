#!/bin/bash

for i in $(ls test);do PYTHONPATH=. python test/$i; done
