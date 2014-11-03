#!/bin/bash
export INSCRIPT=1
export BASE=$PWD
export DATABASE="spritsim"

. $BASE/setup/lib/functions.sh

infoMsg "Creating temporary directory"
mkdir -p $BASE/{bin,tmp}
export TMPDIR=$BASE/tmp


PS3="Select Job to do: "
select job in setup/*.sh "All" "Done"; do
	case "$job" in
		All)
			for f in setup/*.sh; do
				source "$f"
			done
			break;;
		Done)
			break;;
		*)
			source "$job"
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
