# Load required libraries
library(tidyverse)
library(psych)

# Data
files <- c(
    "gators_data/gators-514.csv", "gators_data/gators-667.csv", "gators_data/gators-713.csv", "gators_data/gators-941.csv", "gators_data/gators-565.csv",
    "gators_data/gators-180.csv", "gators_data/gators-227.csv", "gators_data/gators-288.csv", "gators_data/gators-566.csv", "gators_data/gators-944.csv"
)
participant_ids <- c(514, 667, 713, 941, 565, 180, 227, 288, 566, 944) # Replace with actual IDs
groups <- c(rep("static", 5), rep("dynamic", 5)) # Adjust if needed

# Read files into data frame
all_data <- data.frame()
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    df$participant <- participant_ids[i]
    df$group <- groups[i]
    df_sub <- df %>%
        select(participant, group, Item, Rating_response)
    all_data <- bind_rows(all_data, df_sub)
}

# Assign subscale
all_data <- all_data %>%
    mutate(
        subscale = case_when(
            Item >= 1 & Item <= 5 ~ "P+",
            Item >= 6 & Item <= 10 ~ "P-",
            Item >= 11 & Item <= 15 ~ "S+",
            Item >= 16 & Item <= 20 ~ "S-",
            TRUE ~ NA_character_
        ),
        group = factor(group, levels = c("static", "dynamic"))
    )

# Calculate means per participant and subscale
subscale_scores <- all_data %>%
    group_by(participant, group, subscale) %>%
    summarise(mean_rating = mean(Rating_response, na.rm = TRUE), .groups = "drop")

# Calculate mean for whole scale per participant
total_scores <- all_data %>%
    group_by(participant, group) %>%
    summarise(mean_rating = mean(Rating_response, na.rm = TRUE), .groups = "drop") %>%
    mutate(subscale = "Total")

scores <- bind_rows(subscale_scores, total_scores)
scores <- scores %>%
    mutate(subscale = factor(subscale, levels = c("P+", "P-", "S+", "S-", "Total")))

print("Total")
total_dynamic <- scores %>% filter(group == "dynamic", subscale=="Total")
median(total_dynamic$mean_rating)
IQR(total_dynamic$mean_rating)
total_static <- scores %>% filter(group == "static", subscale=="Total")
median(total_static$mean_rating)
IQR(total_static$mean_rating)

print("P+")
p_plus_dynamic <- scores %>% filter(group == "dynamic", subscale=="P+")
median(p_plus_dynamic$mean_rating)
IQR(p_plus_dynamic$mean_rating)
p_plus_static <- scores %>% filter(group == "static", subscale=="P+")
median(p_plus_static$mean_rating)
IQR(p_plus_static$mean_rating)

print("P-")
p_minus_dynamic <- scores %>% filter(group == "dynamic", subscale=="P-")
median(p_minus_dynamic$mean_rating)
IQR(p_minus_dynamic$mean_rating)
p_minus_static <- scores %>% filter(group == "static", subscale=="P-")
median(p_minus_static$mean_rating)
IQR(p_minus_static$mean_rating)

print("S+")
s_plus_dynamic <- scores %>% filter(group == "dynamic", subscale=="S+")
median(s_plus_dynamic$mean_rating)
IQR(s_plus_dynamic$mean_rating)
s_plus_static <- scores %>% filter(group == "static", subscale=="S+")
median(s_plus_static$mean_rating)
IQR(s_plus_static$mean_rating)

print("S-")
s_minus_dynamic <- scores %>% filter(group == "dynamic", subscale=="S-")
median(s_minus_dynamic$mean_rating)
IQR(s_minus_dynamic$mean_rating)
s_minus_static <- scores %>% filter(group == "static", subscale=="S-")
median(s_minus_static$mean_rating)
IQR(s_minus_static$mean_rating)

# Wilcoxon rank-sum for subscales and total
stat_results <- scores %>%
    group_by(subscale) %>%
    summarise(
        p_value = wilcox.test(mean_rating ~ group)$p.value,
        statistic = wilcox.test(mean_rating ~ group)$statistic,
        CI_lower = wilcox.test(mean_rating ~ group, conf.int = TRUE)$conf.int[1],
        CI_upper = wilcox.test(mean_rating ~ group, conf.int = TRUE)$conf.int[2]
    )
print(stat_results)

# Boxplot
condition_palette <- c("static" = "#D62728", "dynamic" = "#17b3b7")
ggplot(scores, aes(x = group, y = mean_rating, fill = group)) +
    geom_boxplot(outlier.shape = NA, alpha = 0.6) +
    geom_jitter(width = 0.1, size = 2, alpha = 0.7) +
    facet_wrap(~ subscale, ncol = 3) +
    labs(title = "GAToRS Subscale and Total Scores by Condition",
         x = "Condition",
         y = "Mean Rating") +
    theme_minimal() +
    theme(legend.position = "none") +
    scale_fill_manual(
        values = condition_palette,
        name = "Condition",
        labels = c("dynamic" = "Adaptive", "static" = "Static")
    ) +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    scale_y_continuous(breaks = seq(0, 4, by = 1), limits = c(0, 4))
