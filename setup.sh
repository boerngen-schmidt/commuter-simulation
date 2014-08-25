#!/bin/bash

INSCRIPT=0
export INSCRIPT
export BASE=$PWD

for f in script.d/*.sh; do
	/bin/bash "$f"
	#/bin/bash $PWD/script.d/$f.sh
done

