library(tidyverse)

# Data
files <- c("handover_data/514_static_handover.csv",
           "handover_data/667_static_handover.csv",
           "handover_data/713_static_handover.csv",
           "handover_data/941_static_handover.csv",
           "handover_data/565_static_handover.csv",
           "handover_data/180_dynamic_handover.csv",
           "handover_data/227_dynamic_handover.csv",
           "handover_data/288_dynamic_handover.csv",
           "handover_data/566_dynamic_handover.csv",
           "handover_data/944_dynamic_handover.csv")
groups <- c(rep("static", 5), rep("dynamic", 5))

all_handovers <- data.frame()

# Read files
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    
    df$participant <- tools::file_path_sans_ext(basename(files[i]))
    df$group <- groups[i]
    
    df$handover_number <- as.numeric(gsub("handover_", "", df$identifier))
    
    df_subset <- df %>% select(participant, group, handover_number, full_duration)
    all_handovers <- bind_rows(all_handovers, df_subset)
}

all_handovers$group <- factor(all_handovers$group, levels = c("static", "dynamic"))

# Median duration by group and trial number
median_durations <- all_handovers %>%
    group_by(group, handover_number) %>%
    summarise(median_duration = median(full_duration, na.rm = TRUE), .groups = "drop")

# Wilcoxon test for overall duration
wilcox_overall <- wilcox.test(median_duration ~ group, data = median_durations, exact = TRUE, correct = FALSE, conf.int = TRUE)
wilcox_overall

# Split data by condition
dynamic_data <- all_handovers %>% filter(group == "dynamic")
static_data <- all_handovers %>% filter(group == "static")

# Group-level stats
median(dynamic_data$full_duration)
IQR(dynamic_data$full_duration)
median(static_data$full_duration)
IQR(static_data$full_duration)

# Plot overall handover duration
ggplot() +
    geom_jitter(data = all_handovers, 
                aes(x = handover_number, y = full_duration, color = group),
                width = 0.2, alpha = 0.5, size = 1.5) +
    # median duration lines per group
    geom_line(data = median_durations, 
              aes(x = handover_number, y = median_duration, color = group), 
              size = 1.2) +
    scale_x_continuous(breaks = seq(0, 40, by = 2)) +
    scale_y_continuous(limits = c(15000, NA)) +
    scale_color_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static" = "Static"
    )) +
    labs(title = "Full Duration of Handovers Over Trials by Condition",
         x = "Trial Number",
         y = "Median Duration (ms)",
         color = "Condition") +
    theme_minimal()
