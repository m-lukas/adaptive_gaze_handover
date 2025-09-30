library(tidyverse)
library(ggpubr)
library(gridExtra)
library(dplyr)

# Data
files <- c("gaze_data/514_static_gaze.csv", "gaze_data/667_static_gaze.csv", "gaze_data/713_static_gaze.csv", "gaze_data/941_static_gaze.csv", "gaze_data/565_static_gaze.csv",
           "gaze_data/180_dynamic_gaze.csv", "gaze_data/227_dynamic_gaze.csv", "gaze_data/288_dynamic_gaze.csv", "gaze_data/566_dynamic_gaze.csv", "gaze_data/944_dynamic_gaze.csv")
groups <- c(rep("static", 5), rep("dynamic", 5))

# Prepare summary data frame
summary_data <- data.frame(
    participant = character(),
    group = character(),
    robot_face_count = numeric(),
    robot_face_mean_duration = numeric(),
    left_handover_count = numeric(),
    left_handover_mean_duration = numeric(),
    right_handover_count = numeric(),
    right_handover_mean_duration = numeric(),
    packaging_count = numeric(),
    packaging_mean_duration = numeric(),
    overall_count = numeric(),
    overall_duration = numeric(),
    stringsAsFactors = FALSE
)

# Read data into dataframe
for (i in seq_along(files)) {
    file <- files[i]
    group <- groups[i]
    
    df <- read.csv(file)
    
    robot_face_data <- df %>% filter(target == "robot_face")
    left_handover_data <- df %>% filter(target == "left_handover_location")
    right_handover_data <- df %>% filter(target == "right_handover_location")
    packaging_data <- df %>% filter(target == "packaging_area")
    
    targets <- c("left_handover_location", "right_handover_location", "packaging_area")
    non_robot_face_data <- df %>% filter(target %in% targets)
    
    robot_face_count <- nrow(robot_face_data)
    robot_face_mean_duration <- ifelse(robot_face_count > 0, mean(robot_face_data$duration), NA)
    
    left_handover_count <- nrow(left_handover_data)
    left_handover_mean_duration <- ifelse(left_handover_count > 0, mean(left_handover_data$duration), NA)
    
    right_handover_count <- nrow(right_handover_data)
    right_handover_mean_duration <- ifelse(right_handover_count > 0, mean(right_handover_data$duration), NA)
    
    packaging_count <- nrow(packaging_data)
    packaging_mean_duration <- ifelse(packaging_count > 0, mean(packaging_data$duration), NA)

    non_robot_face_count <- nrow(non_robot_face_data)
    non_robot_face_mean_duration <- ifelse(non_robot_face_count > 0, mean(non_robot_face_data$duration), NA)
    
    diff_robot_other_count <- non_robot_face_count - robot_face_count
    diff_robot_other_duration <- non_robot_face_mean_duration - robot_face_mean_duration
    
    overall_count = nrow(df)
    overall_duration = mean(df$duration)
    print(paste0(tools::file_path_sans_ext(file), overall_duration))
    
    summary_data <- rbind(summary_data, data.frame(
        participant = tools::file_path_sans_ext(file),
        group = group,
        robot_face_count = robot_face_count,
        robot_face_mean_duration = robot_face_mean_duration,
        left_handover_count = left_handover_count,
        left_handover_mean_duration = left_handover_mean_duration,
        right_handover_count = right_handover_count,
        right_handover_mean_duration = right_handover_mean_duration,
        packaging_count = packaging_count,
        packaging_mean_duration = packaging_mean_duration,
        non_robot_face_count = non_robot_face_count,
        non_robot_face_mean_duration = non_robot_face_mean_duration,
        diff_robot_other_count = diff_robot_other_count,
        diff_robot_other_duration = diff_robot_other_duration,
        overall_count = overall_count,
        overall_duration = overall_duration,
        stringsAsFactors = FALSE
    ))
}

summary_data$group <- factor(summary_data$group, levels = c("static", "dynamic"))

print("-- Robot Face --")
print(paste0("median Count: ", median(summary_data$robot_face_count)))
print(IQR(summary_data$robot_face_count))
print(paste0("median Duration: ", median(summary_data$robot_face_mean_duration)))
print(IQR(summary_data$robot_face_mean_duration))

print("-- Left Handover --")
print(paste0("median Count: ", median(summary_data$left_handover_count)))
print(IQR(summary_data$left_handover_count))
print(paste0("median Duration: ", median(summary_data$left_handover_mean_duration)))
print(IQR(summary_data$left_handover_mean_duration))

print("-- Right Handover --")
print(paste0("median Count: ", median(summary_data$right_handover_count)))
print(IQR(summary_data$right_handover_count))
print(paste0("median Duration: ", median(summary_data$right_handover_mean_duration)))
print(IQR(summary_data$right_handover_mean_duration))

print("-- Packaging Area --")
print(paste0("median Count: ", median(summary_data$packaging_count)))
print(IQR(summary_data$packaging_count))
print(paste0("median Duration: ", median(summary_data$packaging_mean_duration)))
print(IQR(summary_data$packaging_mean_duration))

# robot-face vs other targets Wilcoxon tests
count_face_vs_other <- wilcox.test(summary_data$robot_face_count, summary_data$non_robot_face_count,
                         conf.int = TRUE)
print(count_face_vs_other)
dur_face_vs_other <- wilcox.test(summary_data$robot_face_mean_duration, summary_data$non_robot_face_mean_duration,
                         conf.int = TRUE)
print(dur_face_vs_other)

# robot-face vs other targets median and IQR
print(median(summary_data$diff_robot_other_count))
print(IQR(summary_data$diff_robot_other_count))
print(median(summary_data$diff_robot_other_duration))
print(IQR(summary_data$diff_robot_other_duration))

# robot-face vs other targets Wilcoxon test between-condition
face_other_count_group_test <- wilcox.test(diff_robot_other_count ~ group, data = summary_data, conf.int = TRUE)
face_other_duration_group_test <- wilcox.test(diff_robot_other_duration ~ group, data = summary_data, conf.int = TRUE)

cat("Wilcoxon test for robot_face other count diff:\n")
print(face_other_count_group_test)

cat("\nWilcoxon test for robot_face other duration diff:\n")
print(face_other_duration_group_test)

# Split data by condition
dynamic_data <- summary_data %>% filter(group == "dynamic")
static_data <- summary_data %>% filter(group == "static")

print("Danymic: Face vs Other Diff")
print(median(dynamic_data$diff_robot_other_count))
print(IQR(dynamic_data$diff_robot_other_count))
print(median(dynamic_data$diff_robot_other_duration))
print(IQR(dynamic_data$diff_robot_other_duration))

print("Static: Face vs Other Diff")
print(median(static_data$diff_robot_other_count))
print(IQR(static_data$diff_robot_other_count))
print(median(static_data$diff_robot_other_duration))
print(IQR(static_data$diff_robot_other_duration))

print("Dynamic, Robot Face, Count")
print(median(dynamic_data$robot_face_count))
print(IQR(dynamic_data$robot_face_count))
print(median(dynamic_data$robot_face_mean_duration))
print(IQR(dynamic_data$robot_face_mean_duration))
print("Static, Robot Face, Duration")
print(median(static_data$robot_face_count))
print(IQR(static_data$robot_face_count))
print(median(static_data$robot_face_mean_duration))
print(IQR(static_data$robot_face_mean_duration))

print("Overall Dynamic")
print(median(dynamic_data$overall_count))
print(IQR(dynamic_data$overall_count))
print(median(dynamic_data$overall_duration))
print(IQR(dynamic_data$overall_duration))
print("Overall Static")
print(median(static_data$overall_count))
print(IQR(static_data$overall_count))
print(median(static_data$overall_duration))
print(IQR(static_data$overall_duration))

# Wilcoxon for overall visual sampling
overall_count_test <- wilcox.test(overall_count ~ group, data = summary_data, conf.int = TRUE)
overall_duration_test <- wilcox.test(overall_duration ~ group, data = summary_data, conf.int = TRUE)

cat("Wilcoxon test for overall count:\n")
print(overall_count_test)

cat("\nWilcoxon test for overall duration:\n")
print(overall_duration_test)

# Wilcoxon tests for robot-face fixations
count_test <- wilcox.test(robot_face_count ~ group, data = summary_data, conf.int = TRUE)
duration_test <- wilcox.test(robot_face_mean_duration ~ group, data = summary_data, conf.int = TRUE)

cat("Wilcoxon test for robot_face_count:\n")
print(count_test)

cat("\nWilcoxon test for robot_face_mean_duration:\n")
print(duration_test)

# Visual Sampling Count Boxplot
p_overall_count <- ggplot(summary_data, aes(x = group, y = overall_count, fill = group)) +
    geom_boxplot() +
    geom_point(position = position_dodge(width = 0.75), size = 1) +
    labs(title = "Overall Average Fixation Count by Condition",
         y = "Fixation Count",
         x = "Condition") +
    theme_minimal() +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    theme(legend.position = "none") +
    scale_y_continuous(breaks = seq(400, 600, by = 50), limits = c(400, 600))

# Visual Sampling Duration Boxplot
p_overall_duration <- ggplot(summary_data, aes(x = group, y = overall_duration, fill = group)) +
    geom_boxplot() +
    geom_point(position = position_dodge(width = 0.75), size = 1) +
    labs(title = "Overall Average Fixation Duration by Condition",
         y = "Duration (ms)",
         x = "Condition") +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    theme_minimal() +
    theme(legend.position = "none") +
    scale_y_continuous(breaks = seq(1400, 2200, by = 100), limits = c(1400, 2200))

grid.arrange(p_overall_count, p_overall_duration, ncol=2)

# Robot Face Fixation Count Boxplot
p1 <- ggplot(summary_data, aes(x = group, y = robot_face_count, fill = group)) +
    geom_boxplot() +
    geom_point(position = position_dodge(width = 0.75), size = 1) +
    labs(title = "Robot Face Fixation Count by Condition",
         y = "Fixation Count",
         x = "Condition") +
    theme_minimal() +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    theme(legend.position = "none") +
    scale_y_continuous(breaks = seq(0, 140, by = 20), limits = c(0, 140))

# Robot Face Fixation Duration Boxplot
p2 <- ggplot(summary_data, aes(x = group, y = robot_face_mean_duration, fill = group)) +
    geom_boxplot() +
    geom_point(position = position_dodge(width = 0.75), size = 1) +
    labs(title = "Robot Face Fixation Duration by Condition",
         y = "Duration (ms)",
         x = "Condition") +
    scale_x_discrete(labels = c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    )) +
    theme_minimal() +
    theme(legend.position = "none") +
    scale_y_continuous(breaks = seq(900, 1600, by = 100), limits = c(900, 1600))

grid.arrange(p1, p2, ncol=2)
