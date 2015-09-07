source('database.R')

q <-
  dbSendQuery(
    con, "SELECT ROUND(route_work_distance)::int as distance, array_length(filling_stations, 1)::int as stations FROM de_sim_data_commuter WHERE NOT rerun"
  )
rs <- fetch(q, n = -1)

dbClearResult(q)
dbDisconnect(con)

attach(rs)

lm1 <- lm(stations ~ distance, data = rs)
summary(lm1)

library(ggplot2)
source("functions/ggplot_smooth_func.R")

p1 <- ggplot(rs, aes(x = distance, y = stations)) 
p1 <- p1 + geom_point(size = 1, position = position_jitter(width = 1,height = .5), alpha = 0.4) 
p1 <- p1 + geom_smooth(method = "lm", col = "red") 
p1 <- p1 + ylab("Tankstellen") + xlab("Entfernung") 
p1 <- p1 + stat_smooth_func(geom="text", method="lm", hjust=0, parse=TRUE)

ggsave(filename = "Plots/Tankstellen_Entfernung.png", plot = p1, units = "cm", width = 16, height = 8)