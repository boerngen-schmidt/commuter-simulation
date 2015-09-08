setwd("~/workspace/commuter-simulation/analysis")

#library(xts)
library(lfe)
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
                  refueling_time,
                  EXTRACT(isodow FROM r.refueling_time) as day,
                  EXTRACT(HOUR FROM r.refueling_time)+1 as hour,
                  o.price as oilprice,
                  r.rerun::int as app,
                  EXTRACT(doy FROM r.refueling_time) - EXTRACT(doy FROM '2014-06-01 00:00:00'::timestamp) AS count,
                  CASE WHEN r.fuel_type = 'e5' 
                    THEN ROUND((r.price-0.6545-(r.price-(r.price/1.19)))::numeric, 4)
                    ELSE ROUND((r.price-0.4704-(r.price-(r.price/1.19)))::numeric, 4)
                  END AS net_price,
                  CASE WHEN r.fuel_type = 'e5' 
                    THEN 0.6545
                    ELSE 0.4704
                  END AS fuel_tax,
                  CASE WHEN r.fuel_type = 'e5' 
                    THEN ROUND((r.price-(r.price/1.19))::numeric, 4)
                    ELSE ROUND((r.price-(r.price/1.19))::numeric, 4)
                  END AS vat,
                  r.price,
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
                  SELECT rs_start, rs_end FROM de_sim_routes_outgoing ro
                  LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_start FROM de_sim_points WHERE id = ro.start_point LIMIT 1) s ON TRUE
                  LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_end FROM de_sim_points WHERE id = ro.end_point LIMIT 1) e ON TRUE
                  WHERE ro.id = r.c_id
                  LIMIT 1
                  ) p ON TRUE
                  ORDER BY refueling_time")

observations <- fetch(rs, n = -1)
dbClearResult(rs)
dbCommit(con)
dbDisconnect(con)

# Create eXtended Time Series from queried data
#xts.1 <- xts(x=observations[c("price", "bab_station", "app", "fuel_type", "brand", "oilprice")], order.by=observations$refueling_time)

# remove not needed objects from environment
rm(con, drv, rs)

z.rs_end <- factor(observations$rs_end)
z.rs_station <- factor(observations$rs_station)
z.rs_start <- factor(observations$rs_start)

#rs_start.eff <- rnorm(nlevels(z.rs_start))
#rs_station.eff <- rnorm(nlevels(z.rs_station))
#rs_end.eff <- rnorm(nlevels(z.rs_end))

# Linear Regression with time series
#lm2 <- lm(price ~ app + oilprice + bab_station + fuel_type + brand, data=xts.1)
lm1 <- felm(price ~ app + hour + day + bab_station + brand + oilprice + fuel_type | z.rs_start + z.rs_end + z.rs_station, data=observations)

# Save Information
zz <- file(paste("fit-PricePerLiter_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
sink(zz)
sink(zz, type = "output")

cat("### Summary ###\n\n")
summary(lm1)

cat("\n### The group fixed effects ###\n\n")
getfe(lm1)

cat("\n### Model Coefficients ###\n\n")
coefficients(lm1) # model coefficients

cat("\n### Confidence Intervals for Model Parameters (level=0.99) ###\n\n")
confint(lm1, level=0.99) # CIs for model parameters
#fitted(lm1) # predicted values

cat("\n### Model Residuals ###\n\n")
residuals(lm1) # residuals
#anova(lm1) # anova table

cat("\n### Calculate Variance-Covariance Matrix for a Fitted Model ###\n\n")
vcov(lm1) # covariance matrix for model parameters
#influence(lm1) # regression diagnostics 

## back to the console
sink(type = "message")
sink()
unlink(zz)