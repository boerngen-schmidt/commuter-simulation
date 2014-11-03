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
			return true
		* )
			return false
	esac
}
export -f infoMsg
export -f warnMsg

#### Services

DIST=`gawk -F= '/^NAME/{print tolower($2)}' /etc/os-release`
DIST_GENTOO="gentoo"
# All debian based systems
DIST_DEBIAN="debian" 

function currentDistribution {
	return $DIST
}

function PostgresService {
	
	case currentDistribution in
		$DIST_GENTOO)
			PostgresServiceGentoo $1
			;;
		$DIST_DEBIAN)
			PostgresServiceDebian $1
			;;
}

function PostgresServiceGentoo {
	case $1 in
		start)
			systemctl start postgresql-9.3.service
			;;
		stop)
			systemctl stop postgresql-9.3.service
			;;
		restart)
			systemctl restart postgresql-9.3.service
			;;
	esac
}

function PostgresServiceDebian {
	case $1 in
		start)
			/etc/init.d/postgresql start
			;;
		stop)
			/etc/init.d/postgresql stop
			;;
		restart)
			/etc/init.d/postgresql restart
			;;
	esac
}