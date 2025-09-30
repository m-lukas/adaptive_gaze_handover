library(tidyverse)
library(psych)
library(dplyr)
library(car)

files <- c("agency_data/agency-514.csv", "agency_data/agency-667.csv", "agency_data/agency-713.csv", "agency_data/agency-941.csv", "agency_data/agency-565.csv",
           "agency_data/agency-180.csv", "agency_data/agency-227.csv", "agency_data/agency-288.csv", "agency_data/agency-566.csv", "agency_data/agency-944.csv")
participant_ids <- c(514, 667, 713, 941, 565, 180, 227, 288, 566, 944)
groups <- c(rep("static", 5), rep("dynamic", 5))

all_data <- data.frame()

# Read files
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    
    df$participant <- participant_ids[i]
    df$group <- groups[i]
    
    df_sub <- df %>% select(participant, group, item_text = Text, rating = Rating_response)
    all_data <- bind_rows(all_data, df_sub)
}

all_data <- all_data %>%
    mutate(
        group = factor(group, levels = c("static", "dynamic"))
    )

# Mean rating per participant
participant_summary <- all_data %>%
    group_by(participant, group) %>%
    summarise(mean_rating = mean(rating, na.rm = TRUE))

# Condition split
dynamic_data <- participant_summary %>% filter(group == "dynamic")
static_data <- participant_summary %>% filter(group == "static")

print(paste0("dynamic ", mean(dynamic_data$mean_rating), "  ", median(dynamic_data$mean_rating), "  ", IQR(dynamic_data$mean_rating)))
print(paste0("static ", mean(static_data$mean_rating), "  ", median(static_data$mean_rating), "  ", IQR(static_data$mean_rating)))

# Reshape data
df_wide <- all_data %>%
    select(participant, item_text, rating) %>%
    pivot_wider(names_from = item_text, values_from = rating)

# Wilcoxon test: rating ~ group
wilcox_test <- wilcox.test(mean_rating ~ group, data = participant_summary, conf.int = TRUE)
print(wilcox_test)

# boxplot
condition_palette <- c("static" = "#D62728", "dynamic" = "#17b3b7")
ggplot(participant_summary, aes(x = group, y = mean_rating, fill = group)) +
    geom_boxplot() +
    geom_jitter(width = 0.1) +
    labs(title = "Perceived Agency Scale Rating by Condition",
         y = "Rating",
         x = "Condition") +
    theme_minimal() +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    theme(legend.position = "none") +
    scale_fill_manual(values = condition_palette, name = "Condition") +
    scale_y_continuous(breaks = seq(0, 4, by = 1), limits = c(0, 4))

# Levene's test
levene_mean <- leveneTest(mean_rating ~ group, data = participant_summary, center = mean)
print(levene_mean)
