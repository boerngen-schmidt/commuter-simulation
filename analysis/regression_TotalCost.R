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
