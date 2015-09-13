library(lfe)
library(car)
library(lmtest)

# Database 
source("database.R")

# Linear Regression over part of the dataset
sqlFile <- 'SQL/fit-PricePer100km_sampled.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
rs <- dbSendQuery(con, sql)
obs.sample <- fetch(rs, n = -1)
dbClearResult(rs)
z2.rs_end <- factor(obs.sample$rs_end)
z2.rs_start <- factor(obs.sample$rs_start)
fit.sample <- lm(price100 ~ app + route + driven_distance + filling_stations + fuel_type + morning+midday+afternoon+night + mon+tue+wed+thu+fri + bab_station + brand + z2.rs_start + z2.rs_end, data=obs.sample)

# Linear Regression over full dataset
sqlFile <- 'SQL/fit-PricePer100km.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
rs <- dbSendQuery(con, sql)
obs.total <- fetch(rs, n = -1)
dbClearResult(rs)
#z.rs_end <- factor(observations$rs_end)
#z.rs_station <- factor(observations$rs_station)
#z.rs_start <- factor(observations$rs_start)
fit.total <- felm(price100 ~ app + route + filling_stations + fuel_type + morning+midday+afternoon+night + mon+tue+wed+thu+fri+sat + bab_station + brand | rs_start + rs_end, data=obs.total, exactDOF="rM")

# Disconnect from Database
dbDisconnect(con)


# Save Information
zz <- file(paste("results/","fit-PricePer100km_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
sink(zz, split=TRUE)

cat("### Summary (sampled) ###\n\n")
summary(fit.sample)

cat("### Summary (total) ###\n\n")
summary(fit.total)

cat("\n### Model Coefficients ###\n\n")
cat("## Sample ##\n")
coefficients(fit.sample)
cat("## Total ##\n")
coefficients(fit.total)

cat("\n### Confidence Intervals for Model Parameters (level=0.99) ###\n\n")
cat("## Sample ##\n")
confint(fit.sample, level=0.99)
cat("## Total ##\n")
confint(fit.total, level=0.99)
#fitted(lm1) # predicted values

cat("\n### Model Residuals ###\n\n")
cat("## Sample ##\n")
residuals(fit.total)
cat("## Total ##\n")

cat("\n### Anova Table ###\n\n")
cat("## Sample ##\n")
anova(fit.sample)

cat("\n### Calculate Variance-Covariance Matrix for a Fitted Model ###\n\n")
cat("## Sample ##\n")
vcov(fit.sample)
cat("## Total ##\n")
vcov(fit.total)
#influence(lm1) # regression diagnostics 

cat("\n### The group fixed effects (Total)###\n\n")
getfe(fit.total)

cat("\n### Tests for Model ###\n#######################\n\n")
cat("### Summaries ###\n\n")

cat("\n### Variance Inflation Factor ###\n\n")
vif(fit.sample)

cat("\n### Hetroskedasticity ###\n\n")
bptest(fit.sample)

cat("\n### Autocorrelation ###\n\n")
dwtest(fit.sample)
#summary(lm(lm2$res[-length(lm2$res)] ~ lm2$res[-1]))

## back to the console
sink()