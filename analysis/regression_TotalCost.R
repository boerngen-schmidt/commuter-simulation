# Load Packages
library(car)
library(lmtest)

# Database 
source("database.R")

# Linear Regression over full dataset
sqlFile <- 'SQL/fit-TotalCost.sql'
sql <- readChar(sqlFile, file.info(sqlFile)$size)
obs.total <- dbGetQuery(con, sql)
dbCommit(con)
fit.total <- lm(formula = cost ~ 0 + app + fuel_type + amount + goodtime + brands + bab_stations, data = obs.total)
dbDisconnect(con)

# Save Information
zz <- file(paste("results/","fit-TotalCost_",format(Sys.time(), "%Y-%m-%d %H-%M"), ".txt", sep=""), open = "wt")
sink(zz, split=TRUE)

cat("### Summary ###\n")
summary(fit.total)

cat("\n### Model Coefficients ###\n")
coefficients(fit.total)

cat("\n### Confidence Intervals for Model Parameters (level=0.99) ###\n")
confint(fit.total, level=0.99)
#fitted(lm1) # predicted values

cat("\n### Model Residuals ###\n")
residuals(fit.total)

cat("\n### Anova Table ###\n")
anova(fit.total)

cat("\n### Calculate Variance-Covariance Matrix for a Fitted Model ###\n")
vcov(fit.total)

cat("\n### Tests for Model ###\n#######################\n\n")

cat("### Variance Inflation Factor ###\n")
vif(fit.total)

cat("### Hetroskedasticity ###\n")
bptest(fit.total)

cat("### Autocorrelation ###\n")
dwtest(fit.total)

## back to the console
sink()
rm(zz)