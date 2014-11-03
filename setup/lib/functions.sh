DIST_GENTOO="gentoo"
# All debian based systems
DIST_DEB="debian" 

function currentDistribution {
	return $DISDIST_GENTOO

function PostgresService {
	
	case currentDistribution in
		$DIST_GENTOO)
			PostgresServiceGentoo $1
			;;
		$DIST_DEB)
			PostgresServiceDebian $1
			;;
}

function PostgresServiceGentoo {
	case $1 in
		start)
			systemctl start postgres-9.3
			;;
		stop)
			systemctl stop postgres-9.3
			;;
		restart)
			systemctl restart postgres-9.3
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