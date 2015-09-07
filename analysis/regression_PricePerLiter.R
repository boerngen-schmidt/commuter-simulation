setwd("~/workspace/commuter-simulation/analysis")

#library(xts)
source("database.R")

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
  EXTRACT(isodow FROM r.refueling_time) as day,
  EXTRACT(HOUR FROM r.refueling_time)+1 as hour,
  o.price as oilprice,
  r.rerun::int as app,
  CASE WHEN r.fuel_type = 'e5' 
    THEN ROUND((r.price-0.6545-(r.price-(r.price/1.19)))::numeric, 4)
    ELSE ROUND((r.price-0.4704-(r.price-(r.price/1.19)))::numeric, 4)
  END AS price,
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
  SUBSTRING(s.rs FOR 5) AS rs_station,
  p.rs_start,
  p.rs_end
FROM de_sim_data_refill r
LEFT JOIN de_tt_stations_modified s ON (s.id = r.station)
LEFT JOIN LATERAL (
  SELECT price FROM de_sim_data_oilprice op
  WHERE op.day <= r.refueling_time::date 
  ORDER BY op.day DESC LIMIT 1
) o ON TRUE
LEFT JOIN LATERAL (
  SELECT start_rs, end_rs FROM de_sim_routes_outgoing ro
  LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_start FROM de_sim_points WHERE id = ro.start_point LIMIT 1) s ON TRUE
  LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_end FROM de_sim_points WHERE id = ro.end_point LIMIT 1) e ON TRUE
  WHERE ro.id = r.c_id
  LIMIT 1
) p ON TRUE")

observations <- fetch(rs, n = -1)
dbClearResult(rs)
dbCommit(con)
dbDisconnect(con)

# Create eXtended Time Series from queried data
#xts.1 <- xts(x=data[c("price", "bab_station", "rerun", "fuel_type", "within", "route_length", "brand")], order.by=data$refueling_time, unique=FALSE)

# remove not needed objects from environment
rm(con, drv, rs)

observations$rs_end <- factor(observations$rs_end)
observations$rs_station <- factor(observations$rs_station)
observations$rs_start <- factor(observations$rs_start)

# Linear Regression with time series
#lm1 <- lm(price ~ app + oilprice + hour + day + fuel_type + brand + factor(start_rs) + factor(end_rs) + factor(station), data=data)
lm1 <- felm(price ~ app + oilprice + hour + day + fuel_type + brand | rs_start + rs_station + rs_end, data=observations)

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