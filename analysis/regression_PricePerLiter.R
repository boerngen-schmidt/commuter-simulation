# Load Packages
library(lfe)
library(car)
library(lmtest)

# Database
source("database.R")

# Linear Regression over part of the dataset
sqlFile <- 'SQL/fit-PricePerLiter_sampled+factors.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
obs.sample.factors <- dbGetQuery(con, sql)
f.day. <- as.factor(obs.sample.factors$zeday); f.day. <- relevel(f.day., ref="Mon")
f.time. <- as.factor(x=obs.sample.factors$time_slotted); f.time. <- relevel(f.time., ref="morning")
f.station. <- as.factor(obs.sample.factors$rs_station)
fit.sample <- lm(price ~ app + bab_station + brand + oilprice + fuel_type + f.day. + f.time. + f.station., data=obs.sample.factors)

# Linear Regression over full dataset
sqlFile <- 'SQL/fit-PricePerLiter+factors.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
obs.total <- dbGetQuery(con, sql)
ft.day <- as.factor(obs.total$zeday); ft.day <- relevel(ft.day, ref="Mon")
ft.time <- as.factor(x=obs.total$time_slotted); ft.time <- relevel(ft.time, ref="morning")
ft.station <- as.factor(obs.total$rs_station)
fit.total <- felm(price ~ app + bab_station + brand + oilprice + fuel_type | ft.day + ft.time + ft.station, data=obs.total, exactDOF="rM")

# Disconnect from Database
dbDisconnect(con)


# Save Information
zz <- file(paste("results/","fit-PricePerLiter_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
sink(zz, split=TRUE)

cat("### Summary (sampled) ###\n")
summary(fit.sample)

cat("### Summary (total) ###\n")
summary(fit.total)

cat("\n### Model Coefficients ###\n")
cat("## Sample ##\n")
coefficients(fit.sample)
cat("## Total ##\n")
coefficients(fit.total)

cat("\n### Confidence Intervals for Model Parameters (level=0.99) ###\n\n")
cat("## Sample ##\n")
confint(fit.sample, level=0.99)
cat("## Total ##\n")
confint(fit.total, level=0.99)

cat("\n### Model Residuals ###\n")
cat("## Sample ##\n")
residuals(fit.sample)
cat("## Total ##\n")
residuals(fit.total)

cat("\n### Anova Table ###\n")
cat("## Sample ##\n")
anova(fit.sample)

cat("### Calculate Variance-Covariance Matrix for a Fitted Model ###\n")
cat("## Sample ##\n")
vcov(fit.sample)
cat("## Total ##\n")
vcov(fit.total)

cat("### The group fixed effects (Total)###\n")
getfe(fit.total, ef="zm", robust=TRUE)

cat("### Tests for Model ###\n#######################\n")

cat("### Variance Inflation Factor ###\n")
vif(fit.sample)

cat("### Hetroskedasticity ###\n")
bptest(fit.sample)

cat("### Autocorrelation ###\n")
dwtest(fit.sample)

## back to the console
sink()
rm(zz)