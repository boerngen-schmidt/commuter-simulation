library(lfe)
library(car)
library(lmtest)

# Database 
source("database.R")
sqlFile <- 'SQL/fit-TotalCost.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
rs <- dbSendQuery(con, sql)
observations <- fetch(rs, n = -1)
dbClearResult(rs)
dbDisconnect(con)

# remove not needed objects from environment
rm(con, drv, rs)

# Linear Regression over full dataset

z.rs_end <- factor(observations$rs_end)
z.rs_station <- factor(observations$rs_station)
z.rs_start <- factor(observations$rs_start)
lm1 <- felm(cost ~ app + refill_events + filling_stations + fuel_type 
            + mon_morning+mon_midday+mon_afternoon+mon_night 
            + tue_morning+tue_midday+tue_afternoon+tue_night 
            + wed_morning+wed_midday+wed_afternoon 
            + thu_morning+thu_midday+thu_afternoon+thu_night 
            + fri_morning+fri_midday+fri_afternoon 
            + sat_morning+sat_midday+sat_afternoon 
            + bab_station + brand | rs_start + rs_end, data=observations)

# Linear Regression over part of the dataset
source("database.R")
sqlFile <- 'SQL/fit-TotalCost-time_sampled.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
rs <- dbSendQuery(con, sql)
obs <- fetch(rs, n = -1)
dbClearResult(rs)
dbDisconnect(con)

#obs.merged <- rbind(subset(observations, app == 1)[1:50000, ], subset(observations, app == 0)[1:50000, ])
z2.rs_end <- factor(obs$rs_end)
z2.rs_start <- factor(obs$rs_start)
z2.c_id <- factor(obs$c_id)
lm2 <- lm(cost ~ app + driven_distance + filling_stations + fuel_type 
          + mon_morning+mon_midday+mon_afternoon
          + tue_morning+tue_midday+tue_afternoon
          + wed_morning+wed_midday+wed_afternoon 
          + thu_morning+thu_midday+thu_afternoon
          + fri_morning+fri_midday+fri_afternoon 
          + sat_morning+sat_midday+sat_afternoon 
          + bab_station + brand + z2.rs_start, data=obs)


# Save Information
zz <- file(paste("results/","fit-TotalCost_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
sink(zz, split=TRUE)

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

cat("\n### Tests for Model ###\n#######################\n\n")
cat("### Summaries ###\n\n")

cat("\n### Variance Inflation Factor ###\n\n")
vif(lm2)

cat("\n### Hetroskedasticity ###\n\n")
bptest(lm2)

cat("\n### Autocorrelation ###\n\n")
dwtest(lm2)
summary(lm(lm2$res[-length(lm2$res)] ~ lm2$res[-1]))

## back to the console
sink()