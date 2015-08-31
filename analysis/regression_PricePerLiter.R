setwd("~/workspace/commuter-simulation/analysis")

library(RPostgreSQL)
library(xts)

source("database.R")

drv <- dbDriver("PostgreSQL")
con <- dbConnect(drv, host=db.host, dbname=db.name, user=db.user, password=db.pass)

# Database 
dbSendQuery(con, "BEGIN")
dbSendQuery(con, "CREATE TEMP TABLE bab_stations AS 
                    SELECT id 
                    FROM de_tt_stations_modified 
                    WHERE LOWER(street) ~  '(a\\d+|a\\s+\\d+|bab|autohof|rasthof|autobahn|^a$)' OR LOWER(name) ~ 'bat'")
dbSendQuery(con, "CREATE TEMP TABLE brands AS 
                    SELECT brand, count(brand) 
                    FROM de_tt_stations_modified 
                    WHERE LOWER(brand) NOT IN ('bft', 'freie tankstelle')
                    GROUP BY brand 
                    HAVING COUNT(brand) > 200")
rs <- dbSendQuery(con, "
SELECT
  r.c_id,
  r.refueling_time, 
  r.rerun::int,
  price,
  ROUND(c.route_work_distance::numeric, 1) AS route_length,
  CASE WHEN EXISTS(SELECT 1 FROM bab_stations WHERE id = r.station)
    THEN 1
    ELSE 0
  END as bab_station,
  CASE WHEN EXISTS(SELECT 1 FROM de_tt_stations_modified WHERE id = r.station AND brand IN (SELECT brand FROM brands))
    THEN 1
    ELSE 0
  END as brand,
  CASE WHEN r.fuel_type = 'e5' 
    THEN 1 
    ELSE 0 
  END AS fuel_type,
  CASE WHEN EXISTS(SELECT 1 FROM de_sim_routes_within_sampled WHERE commuter = r.c_id)
    THEN 1 
    ELSE 0 
  END AS within
FROM de_sim_data_refill r
LEFT JOIN de_sim_data_commuter c USING(c_id)
ORDER BY refueling_time")

data <- fetch(rs, n = -1)
dbClearResult(rs)
dbCommit(con)
dbDisconnect(con)

# Create eXtended Time Series from queried data
xts.1 <- xts(x=data[c("price", "bab_station", "rerun", "fuel_type", "within", "route_length", "brand")], order.by=data$refueling_time, unique=FALSE)

# remove not needed objects from environment
rm(con, drv, rs, data) 

# Linear Regression with time series
lm1 <- lm(price ~ bab_station + rerun + fuel_type + route_length + within + brand, data=xts.1)

# Save Information
sink(file="lm1.txt", append=FALSE)
summary(lm1)
coefficients(lm1) # model coefficients
confint(lm1, level=0.99) # CIs for model parameters
fitted(lm1) # predicted values
residuals(lm1) # residuals
anova(lm1) # anova table
vcov(lm1) # covariance matrix for model parameters
#influence(lm1) # regression diagnostics 