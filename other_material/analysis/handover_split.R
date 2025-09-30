library(tidyverse)

# Files
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

# Trial classification (left/right)
classification <- read.csv("handover_data/object_classification.csv", header = TRUE)

# Read files
all_handovers <- data.frame()
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    
    df$participant <- tools::file_path_sans_ext(basename(files[i]))
    df$group <- groups[i]
    
    df$handover_number <- seq_len(nrow(df))
    
    df$tray_side <- classification$side[df$handover_number]
    df_subset <- df %>% select(participant, group, handover_number, tray_side, full_duration)
    all_handovers <- bind_rows(all_handovers, df_subset)
}

all_handovers$group <- factor(all_handovers$group, levels = c("static", "dynamic"))
all_handovers$tray_side <- factor(all_handovers$tray_side, levels = c("left", "right"))

# Split data by condition and tray_side
dynamic_data_left <- all_handovers %>% filter(group == "dynamic", tray_side=="left")
static_data_left <- all_handovers %>% filter(group == "static", tray_side=="left")
dynamic_data_right <- all_handovers %>% filter(group == "dynamic", tray_side=="right")
static_data_right <- all_handovers %>% filter(group == "static", tray_side=="right")

# Left-Tray
median(dynamic_data_left$full_duration)
IQR(dynamic_data_left$full_duration)
median(static_data_left$full_duration)
IQR(static_data_left$full_duration)

# Right-Tray
median(dynamic_data_right$full_duration)
IQR(dynamic_data_right$full_duration)
median(static_data_right$full_duration)
IQR(static_data_right$full_duration)

# Calculate median full_duration per group, tray_side, and trial number
median_durations <- all_handovers %>%
    group_by(group, tray_side, handover_number) %>%
    summarise(median_duration = median(full_duration, na.rm = TRUE), .groups = "drop")

# Wilcoxon test for tray_side median duration
wilcox_by_side <- median_durations %>%
    group_split(tray_side) %>%
    setNames(levels(median_durations$tray_side)) %>%
    map(~ wilcox.test(median_duration ~ group, data = .x, , conf.int = TRUE))

wilcox_by_side$left
wilcox_by_side$right

# Medians grouped by participant, group and tray_side
medians_pp <- all_handovers %>%
    group_by(participant, group, tray_side) %>%
    summarise(median_duration = median(full_duration, na.rm = TRUE), .groups = "drop")

# Change df orientation
medians_wide <- medians_pp %>%
    tidyr::pivot_wider(names_from = tray_side, values_from = median_duration)

# Within-condition wilcoxon tests: left vs right
by_group_wilcox <- medians_wide %>%
    group_split(group) %>%
    lapply(function(df) wilcox.test(df$left, df$right, paired = TRUE))

# Difference-in-differences: does left–right difference vary by condition?
diffs <- medians_wide %>%
    mutate(lr_diff = left - right)

wilcox.test(lr_diff ~ group, data = diffs, conf.int = TRUE)

# Plot left tray handover durations
p_left <- ggplot() +
    geom_jitter(data = all_handovers %>% filter(tray_side == "left"), 
                aes(x = handover_number, y = full_duration, color = group),
                width = 0.2, alpha = 0.5, size = 1.5) +
    geom_line(data = median_durations %>% filter(tray_side == "left"),
              aes(x = handover_number, y = median_duration, color = group),
              size = 1.2) +
    scale_y_continuous(limits = c(15000, 35100)) +
    scale_color_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static" = "Static"
    )) +
    labs(title = "Full Duration of Left Tray Handovers",
         x = "Handover Number",
         y = "Median Duration (ms)",
         color = "Condition") +
    theme_minimal()  +
    theme(legend.position = "none")

# Plot right tray handover durations
p_right <- ggplot() +
    geom_jitter(data = all_handovers %>% filter(tray_side == "right"), 
                aes(x = handover_number, y = full_duration, color = group),
                width = 0.2, alpha = 0.5, size = 1.5) +
    geom_line(data = median_durations %>% filter(tray_side == "right"),
              aes(x = handover_number, y = median_duration, color = group),
              size = 1.2) +
    scale_y_continuous(limits = c(15000, 35100)) +
    scale_color_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static" = "Static"
    )) +
    labs(title = "Full Duration of Right Tray Handovers",
         x = "Handover Number",
         y = NULL,
         color = "Condition") +
    theme_minimal()

# Grid arrange with different widths
library(gridExtra)
library(cowplot)
plot_grid(p_left, p_right, align = "h", ncol = 2, rel_widths = c(14/32, 18/32))
