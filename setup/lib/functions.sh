#!/bin/sh
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

function ynQuestion {
	echo; echo;
	read -p "$1 [y/N]: " yn
	case $yn in
		[Yy]* ) 
			echo 1
			;;
		*)
			echo 0
			;;
	esac
}

function doemerge {
	sudo emerge -uav $1
	if [ $? -ne 0 ]; then
		warnMsg "Please fix emerge errors"
		exit 1
	fi
}

#### Services

DIST=`gawk -F= '/^NAME/{print tolower($2)}' /etc/os-release`
DIST_GENTOO="gentoo"
# All debian based systems
DIST_DEBIAN="debian"

function currentDistribution {
	echo $DIST
}

function PostgresService {
	
	case currentDistribution in
		$DIST_GENTOO)
			PostgresServiceGentoo $1
			;;
		$DIST_DEBIAN)
			PostgresServiceDebian $1
			;;
	esac
}

function PostgresServiceGentoo {
	case $1 in
		start)
			sudo systemctl start postgresql-9.5.service
			;;
		stop)
			sudo systemctl stop postgresql-9.5.service
			;;
		restart)
			sudo systemctl restart postgresql-9.5.service
			;;
	esac
}

function PostgresServiceDebian {
	case $1 in
		start)
			sudo /etc/init.d/postgresql start
			;;
		stop)
			sudo /etc/init.d/postgresql stop
			;;
		restart)
			sudo /etc/init.d/postgresql restart
			;;
	esac
}