#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

infoMsg "Running pre-import script"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/pre-import_de_commuter.sql

infoMsg "Importing commuter data for de_commuter_kreise"
copy_kreise="\copy de_commuter_kreise (rs,name,within,home,incoming,outgoing) FROM $BASE/data/commuter/commuter_kreise.csv csv header delimiter ';'"
echo $copy_kreise | psql -U $USER -d $DATABASE -q

infoMsg "Importing commuter data for de_commuter_kreise"
copy_gemeinde="\copy de_commuter_gemeinden (rs,name,within,home,incoming,outgoing) FROM $BASE/data/commuter/commuter_gemeinden.csv csv header delimiter ';'"
echo $copy_gemeinde | psql -U $USER -d $DATABASE -q

infoMsg "Running post-import script"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/post-import_de_commuter.sql