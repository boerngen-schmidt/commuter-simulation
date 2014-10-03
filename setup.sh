#!/bin/bash

export COLOR_NC='\e[0m' # No Color
export COLOR_WHITE='\e[1;37m'
export COLOR_BLACK='\e[0;30m'
export COLOR_BLUE='\e[0;34m'
export COLOR_LIGHT_BLUE='\e[1;34m'
export COLOR_GREEN='\e[0;32m'
export COLOR_LIGHT_GREEN='\e[1;32m'
export COLOR_CYAN='\e[0;36m'
export COLOR_LIGHT_CYAN='\e[1;36m'
export COLOR_RED='\e[0;31m'
export COLOR_LIGHT_RED='\e[1;31m'
export COLOR_PURPLE='\e[0;35m'
export COLOR_LIGHT_PURPLE='\e[1;35m'
export COLOR_BROWN='\e[0;33m'
export COLOR_YELLOW='\e[1;33m'
export COLOR_GRAY='\e[0;30m'
export COLOR_LIGHT_GRAY='\e[0;37m'

function infoMsg {
	echo -e "\e[92m$1 \e[39m..."
}

function warnMsg {
	echo -e "$COLOR_RED$1 $COLOR_NC..."
}
export -f infoMsg
export -f warnMsg
export INSCRIPT=1
export BASE=$PWD
export DATABASE="spritsim"

infoMsg "Creating temporary directory"
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
