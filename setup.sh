#!/bin/bash
export INSCRIPT=1
export BASE=$PWD
export DATABASE="spritsim"

. $BASE/setup/lib/functions.sh

infoMsg "Creating temporary directory"
mkdir -p $BASE/{bin,tmp}
export TMPDIR=$BASE/tmp

echo -e "${COLOR_PURPLE}Main Menu${COLOR_NC}"
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
	echo; echo;
	echo -e "${COLOR_PURPLE}Main Menu${COLOR_NC}"
done

echo; echo;

if [ $(ynQuestion "Do you wish to clean the temporary files?") ]; then
	rm -rf $TMPDIR
fi