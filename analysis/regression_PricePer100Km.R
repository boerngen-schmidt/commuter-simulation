library(lfe)
library(car)
library(lmtest)

# Database 
source("database.R")
sqlFile <- 'SQL/fit-PricePer100km.sql'
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
lm1 <- felm(price100 ~ app + route + filling_stations + fuel_type + morning+midday+afternoon+night + mon+tue+wed+thu+fri+sat + bab_station + brand | rs_start + rs_end, data=observations, exactDOF="rM")

# Linear Regression over part of the dataset
obs.merged <- rbind(subset(observations, app == 1)[1:50000, ], subset(observations, app == 0)[1:50000, ])
z2.rs_end <- factor(obs.merged$rs_end)
z2.rs_start <- factor(obs.merged$rs_start)
lm2 <- lm(price100 ~ app + route + driven_distance + filling_stations + fuel_type + morning+midday+afternoon+night + mon+tue+wed+thu+fri + bab_station + brand + z2.rs_start + z2.rs_end, data=obs.merged)


# Save Information
zz <- file(paste("results/","fit-PricePer100km_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
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