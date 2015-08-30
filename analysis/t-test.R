library(RPostgreSQL)
source("database.R")

## loads the PostgreSQL driver
drv <- dbDriver("PostgreSQL")

## Open a connection
con <- dbConnect(drv, host=db.host, dbname=db.name, user=db.user, password=db.pass)

## T-Test mit Gesamtausgaben für Kraftstoff
query <-"
SELECT * FROM (
  SELECT c_id FROM de_sim_data_commuter WHERE NOT rerun
) c
LEFT JOIN LATERAL (
SELECT SUM(amount*price) as noapp FROM de_sim_data_refill WHERE c_id = c.c_id AND NOT rerun
) p1 ON TRUE
LEFT JOIN LATERAL (
SELECT SUM(amount*price) as app FROM de_sim_data_refill WHERE c_id = c.c_id AND rerun
) p2 ON TRUE"
rs <- dbSendQuery(con, query)
stichproben = fetch(rs,n=-1)
attach(stichproben)
test.sum <- t.test(x=noapp, y=app, paired = TRUE, conf.level = 0.995)
detach(stichproben)


## Preis pro Kilometer
query <-"
SELECT c_id, noapp::float/k.driven_distance AS ppkm_noapp, app::float/n.driven_distance AS ppkm_app FROM (
	(
SELECT c_id, driven_distance FROM de_sim_data_commuter WHERE NOT rerun ORDER BY c_id
) c1
LEFT JOIN LATERAL (
SELECT SUM(amount*price) as noapp FROM de_sim_data_refill WHERE c_id = c1.c_id AND NOT rerun
) p1 ON TRUE
) k
LEFT JOIN (
(
  SELECT c_id, driven_distance FROM de_sim_data_commuter WHERE rerun ORDER BY c_id
) c2
  LEFT JOIN LATERAL (
  SELECT SUM(amount*price) as app FROM de_sim_data_refill WHERE c_id = c2.c_id AND rerun
  ) p2 ON TRUE
) n USING (c_id)
  WHERE app IS NOT NULL AND noapp IS NOT NULL"
rs <- dbSendQuery(con, query)
stichproben = fetch(rs,n=-1)
attach(stichproben)
test.ppkm <- t.test(x=ppkm_noapp, y=ppkm_app, paired = TRUE, conf.level = 0.995)
detach(stichproben)

## Closes the connection
dbDisconnect(con)

## Frees all the resources on the driver
