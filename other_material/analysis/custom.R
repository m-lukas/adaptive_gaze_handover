library(tidyverse)
library(dplyr)

files <- c("custom_data/custom-514.csv", "custom_data/custom-667.csv", "custom_data/custom-713.csv", "custom_data/custom-941.csv", "custom_data/custom-565.csv",
           "custom_data/custom-180.csv", "custom_data/custom-227.csv", "custom_data/custom-288.csv", "custom_data/custom-566.csv", "custom_data/custom-944.csv")
participant_ids <- c(514, 667, 713, 941, 565, 180, 227, 288, 566, 944)
groups <- c(rep("static", 5), rep("dynamic", 5)) # Adjust as needed

# Read files
all_data <- data.frame()
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    df$participant <- participant_ids[i]
    df$group <- groups[i]
    df_sub <- df %>%
        select(participant, group, Item, Rating_response)
    all_data <- bind_rows(all_data, df_sub)
}

item_map <- c(
    `1` = "C1 (smooth handover)",
    `2` = "C2 (movements\ncomplemented)",
    `3` = "C3 (good rhythm)",
    `4` = "C4 (natural gaze)",
    `5` = "C5 (human-like gaze)",
    `6` = "C6 (understanding\nthrough gaze)"
)

all_data <- all_data %>%
    mutate(
        Item = as.integer(Item),
        item_label = factor(
            item_map[as.character(Item)],
            levels = item_map[as.character(sort(unique(Item)))]
        ),
        group = factor(group, levels = c("static", "dynamic"))
    )

item_1_dynamic <- all_data %>% filter(group == "dynamic", Item=="1")
item_2_dynamic <- all_data %>% filter(group == "dynamic", Item=="2")
item_3_dynamic <- all_data %>% filter(group == "dynamic", Item=="3")
item_4_dynamic <- all_data %>% filter(group == "dynamic", Item=="4")
item_5_dynamic <- all_data %>% filter(group == "dynamic", Item=="5")
item_6_dynamic <- all_data %>% filter(group == "dynamic", Item=="6")

item_1_static <- all_data %>% filter(group == "static", Item=="1")
item_2_static <- all_data %>% filter(group == "static", Item=="2")
item_3_static <- all_data %>% filter(group == "static", Item=="3")
item_4_static <- all_data %>% filter(group == "static", Item=="4")
item_5_static <- all_data %>% filter(group == "static", Item=="5")
item_6_static <- all_data %>% filter(group == "static", Item=="6")

print(paste0("1 Dynamic ",median(item_1_dynamic$Rating_response),"  ",IQR(item_1_dynamic$Rating_response)))
print(paste0("2 Dynamic ",median(item_2_dynamic$Rating_response),"  ",IQR(item_2_dynamic$Rating_response)))
print(paste0("3 Dynamic ",median(item_3_dynamic$Rating_response),"  ",IQR(item_3_dynamic$Rating_response)))
print(paste0("4 Dynamic ",median(item_4_dynamic$Rating_response),"  ",IQR(item_4_dynamic$Rating_response)))
print(paste0("5 Dynamic ",median(item_5_dynamic$Rating_response),"  ",IQR(item_5_dynamic$Rating_response)))
print(paste0("6 Dynamic ",median(item_6_dynamic$Rating_response),"  ",IQR(item_6_dynamic$Rating_response)))

print(paste0("1 Static ",median(item_1_static$Rating_response),"  ",IQR(item_1_static$Rating_response)))
print(paste0("2 Static ",median(item_2_static$Rating_response),"  ",IQR(item_2_static$Rating_response)))
print(paste0("3 Static ",median(item_3_static$Rating_response),"  ",IQR(item_3_static$Rating_response)))
print(paste0("4 Static ",median(item_4_static$Rating_response),"  ",IQR(item_4_static$Rating_response)))
print(paste0("5 Static ",median(item_5_static$Rating_response),"  ",IQR(item_5_static$Rating_response)))
print(paste0("6 Static ",median(item_6_static$Rating_response),"  ",IQR(item_6_static$Rating_response)))

# Item Means
question_means <- all_data %>%
    mutate(group = factor(group, levels = c("static", "dynamic"))) %>%
    group_by(Item, item_label, group) %>%
    summarise(mean_rating = mean(Rating_response, na.rm = TRUE), .groups = "drop")

condition_palette <- c("static" = "#D62728", "dynamic" = "#17b3b7")

# Barchart
ggplot(question_means, aes(x = factor(item_label), y = mean_rating, fill = group)) +
    geom_col(position = position_dodge(width = 0.7), width = 0.6) +
    labs(title = "Mean Rating per Custom Item by Condition",
         x = "Item",
         y = "Mean Rating") +
    theme_minimal() +
    scale_fill_manual(
        values = condition_palette,
        name = "Condition",
        labels = c("dynamic" = "Adaptive", "static" = "Static")
    ) +
    scale_y_continuous(breaks = seq(0, 4, by = 1), limits = c(0, 4))

# Wilcox tests
stat_results <- all_data %>%
    group_by(Item) %>%
    summarise(
        p_value = wilcox.test(Rating_response ~ group)$p.value,
        statistic = wilcox.test(Rating_response ~ group)$statistic,
        CI_lower = wilcox.test(Rating_response ~ group, conf.int = TRUE)$conf.int[1],
        CI_upper = wilcox.test(Rating_response ~ group, conf.int = TRUE)$conf.int[2]
    )
print(stat_results)
