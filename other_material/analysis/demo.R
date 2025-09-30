library(tidyverse)
library(psych)

files <- c("demo_data/demo-514.csv", "demo_data/demo-713.csv", "demo_data/demo-941.csv", "demo_data/demo-565.csv", "demo_data/demo-667.csv",
           "demo_data/demo-180.csv", "demo_data/demo-227.csv", "demo_data/demo-288.csv", "demo_data/demo-566.csv", "demo_data/demo-944.csv")
participant_ids <- c(514, 713, 941, 565, 667, 180, 227, 288, 566, 944)
groups <- c(rep("static", 5), rep("dynamic", 5))

# Read files
all_data <- data.frame()
for (i in seq_along(files)) {
    df <- read.csv(files[i])
    
    df$participant <- participant_ids[i]
    df$group <- groups[i]
    
    df_sub <- df %>% select(participant, group, age, gender, education, experience)
    all_data <- bind_rows(all_data, df_sub)
}

# Plot of gender
barplot(table(all_data$gender))
title(main="Gender", ylab="Number of Participants")

# Histogram for age
hist(all_data$age, breaks=8, main="Age of Participant", xlab="Age", ylab="Number of Participants")
mean(all_data$age)
sd(all_data$age)

# Barchart for experience
barplot(table(all_data$experience))
title(main="Experience", ylab="Number of Participants")

# Barchart for education
barplot(table(all_data$education))
title(main="Education", ylab="Number of Participants")

# Barchart for education
condition_palette <- c("static" = "#D62728", "dynamic" = "#17b3b7")
ggplot(all_data, aes(x = factor(experience), fill = group)) +
    geom_bar(position = position_dodge(width = 0.7), width = 0.6) +
    labs(
        title = "Prior Experience with Robots by Condition",
        x = "Prior Robot Experience",
        y = "Number of Participants"
    ) +
    theme_minimal() +
    scale_fill_manual(
        values = condition_palette,
        name = "Condition",
        labels = c("dynamic" = "Adaptive", "static" = "Static")
    )

