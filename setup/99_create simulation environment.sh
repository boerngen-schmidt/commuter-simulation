#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

infoMsg "Creating Table for start and end points"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/de_sim_points.sql

infoMsg "Creating Table for routes"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/de_sim_routes.sql

infoMsg "Creating Table for simulation data"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/de_sim_data.sql