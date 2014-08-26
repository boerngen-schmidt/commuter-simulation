#!/bin/bash

export INSCRIPT=1
export BASE=$PWD
export DATABASE="spritsim"

echo "Creating temporary directory ..."
mkdir -p $BASE/tmp
mkdir -p $BASE/bin
export TMPDIR=$BASE/tmp


PS3="Select Job to do: "
select job in setup/*.sh "All" "Done"; do
	case "$job" in
		All)
			for f in setup/*.sh; do
				/bin/bash "$f"
			done
			break;;
		Done)
			break;;
		*)
			/bin/bash "$job"
	esac
	REPLY=
done

echo; echo;
PS3="Do you wish to clean the temporary files? "
select yn in "Yes" "No"; do
	case "$yn" in
		Yes) 
        	rm -rf $TMPDIR
        	break;;
        No) 
			break;;
		*)
			REPLY=
			;;
	esac
done
