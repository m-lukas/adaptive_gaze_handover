df <- read.csv("figures/packaging_density_local_minima.csv", stringsAsFactors = FALSE)
mean_x <- mean(df$x_min_s)
mean_y <- mean(df$y_min)

mean_x
mean_y