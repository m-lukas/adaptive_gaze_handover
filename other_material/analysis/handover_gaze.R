library("dplyr"); library("purrr"); library("readr"); library("tidyr")
pkgs <- c("dplyr", "purrr", "readr", "tidyr", "tidyverse", "lubridate", "janitor", "scales", "cowplot", "glue", "lme4", "lmerTest", "broom.mixed")
to_install <- pkgs[!pkgs %in% installed.packages()[, "Package"]]
if (length(to_install)) install.packages(to_install, dependencies = TRUE)
invisible(lapply(pkgs, library, character.only = TRUE))

# Files
handover_files <- c("handover_data/180_dynamic_handover.csv",
                    "handover_data/227_dynamic_handover.csv",
                    "handover_data/288_dynamic_handover.csv",
                    "handover_data/566_dynamic_handover.csv",
                    "handover_data/944_dynamic_handover.csv",
                    "handover_data/514_static_handover.csv",
                    "handover_data/667_static_handover.csv",
                    "handover_data/713_static_handover.csv",
                    "handover_data/941_static_handover.csv",
                    "handover_data/565_static_handover.csv")

gaze_files <- c("gaze_data/180_dynamic_gaze.csv",
                "gaze_data/227_dynamic_gaze.csv",
                "gaze_data/288_dynamic_gaze.csv",
                "gaze_data/566_dynamic_gaze.csv",
                "gaze_data/944_dynamic_gaze.csv",
                "gaze_data/514_static_gaze.csv",
                "gaze_data/667_static_gaze.csv",
                "gaze_data/713_static_gaze.csv",
                "gaze_data/941_static_gaze.csv",
                "gaze_data/565_static_gaze.csv")
participants <- c("180", "227", "288", "566", "944", "514", "667", "713", "941", "565")
groups <- c(rep("dynamic", 5), rep("static", 5)) # make sure this order matches your files

# Group from filename
get_meta_from_path <- function(path) {
    fn <- basename(path)
    id <- str_extract(fn, "(?<=^|_)\\d{3}(?=_)")
    cond <- case_when(
        str_detect(fn, "dynamic") ~ "dynamic",
        str_detect(fn, "static") ~ "static",
        TRUE ~ NA_character_
    )
    tibble(file = path, participant = id, condition = cond)
}

handover_meta <- map_dfr(handover_files, get_meta_from_path)
gaze_meta     <- map_dfr(gaze_files,     get_meta_from_path)

meta_pairs <- inner_join(handover_meta, gaze_meta, by = c("participant", "condition"),
                         suffix = c("_handover", "_gaze"))

# Functions for reading files
read_handover <- function(path) {
    df <- read_csv(path, show_col_types = FALSE) %>% clean_names()
    # Parse timestamps
    if ("initiation" %in% names(df)) {
        df <- df %>%
            mutate(initiation = ymd_hms(initiation)) %>%
            mutate(trial = row_number())
    } else {
        stop(glue("initiation column missing in {path}"))
    }
    df
}

read_gaze <- function(path) {
    df <- read_csv(path, show_col_types = FALSE) %>% clean_names()
    if ("start_time" %in% names(df)) {
        df <- df %>%
            mutate(start_time = ymd_hms(start_time)) %>%
            mutate(end_time = start_time + duration/1000) # duration ms -> seconds
    } else {
        stop(glue("start_time column missing in {path}"))
    }
    df
}

# Assign trial number based on handover data row
assign_trials <- function(gaze_df, hand_df) {
    hand_key <- hand_df %>%
        arrange(initiation) %>%
        mutate(next_initiation = lead(initiation))
    
    library(data.table)
    gdt <- as.data.table(gaze_df)
    hdt <- as.data.table(hand_key)
    setkey(hdt, initiation)
    
    # Assign trial = max initiation <= start_time
    ans <- hdt[gdt, roll = TRUE, on = .(initiation = start_time)]
    out <- cbind(gaze_df, ans[, .(trial, initiation, next_initiation)])
    
    # Ignore gaze data before and after task
    out <- out %>%
        filter(!is.na(trial))
    out
}

# Per-trial metrics for robot-face
summarise_trial_metrics <- function(gaze_with_trials, hand_df) {
    face <- gaze_with_trials %>%
        filter(target == "robot_face") %>%
        mutate(duration_s = duration / 1000)
    
    hand_key <- hand_df %>%
        arrange(trial) %>%
        mutate(trial_start = initiation,
               trial_end_nominal = lead(initiation)) %>%
        mutate(full_duration_s = ifelse(is.numeric(full_duration), full_duration/1000, NA_real_)) %>%
        mutate(default_trial_len = median(full_duration_s, na.rm = TRUE),
               trial_end = if_else(is.na(trial_end_nominal) & !is.na(default_trial_len),
                                   trial_start + seconds(default_trial_len),
                                   trial_end_nominal)) %>%
        select(trial, trial_start, trial_end, full_duration_s)
    
    # Compute time within trial
    face_join <- face %>% left_join(hand_key, by = "trial")
    
    face_intervals <- face_join %>%
        mutate(overlap_start = pmax(start_time, trial_start),
               overlap_end   = pmin(end_time, trial_end),
               overlap_s     = as.numeric(pmax(0, overlap_end - overlap_start), units = "secs"),
               mid_time      = start_time + duration_s/2,
               rel_mid_s     = as.numeric(mid_time - trial_start, units = "secs")) %>%
        filter(!is.na(trial_start)) # keep only fixations that map into some trial
    
    # Trial-level aggregation
    trial_face <- face_intervals %>%
        group_by(trial) %>%
        summarise(
            face_fix_count = n(),
            face_total_s = sum(overlap_s, na.rm = TRUE),
            face_mean_s = mean(duration_s, na.rm = TRUE),
            face_median_s = median(duration_s, na.rm = TRUE),
            rel_mid_s_mean = mean(rel_mid_s, na.rm = TRUE),
            rel_mid_s_median = median(rel_mid_s, na.rm = TRUE),
            .groups = "drop"
        )
    
    trial_all <- hand_key %>%
        left_join(trial_face, by = "trial") %>%
        mutate(across(c(face_fix_count, face_total_s, face_mean_s, face_median_s,
                        rel_mid_s_mean, rel_mid_s_median), ~replace_na(., 0))) %>%
        mutate(trial_len_s = as.numeric(trial_end - trial_start, units = "secs"),
               face_prop_of_trial = if_else(!is.na(trial_len_s) & trial_len_s > 0,
                                            face_total_s / trial_len_s, NA_real_))
    
    list(face_intervals = face_intervals, trial_summary = trial_all)
}

# Compute results for all participants
all_face_intervals <- list()
all_trial_summary  <- list()
problems <- c()

for (i in seq_len(nrow(meta_pairs))) {
    ph <- meta_pairs$file_handover[i]
    pg <- meta_pairs$file_gaze[i]
    pid <- meta_pairs$participant[i]
    cond <- meta_pairs$condition[i]
    
    message(glue("Processing participant {pid} ({cond})"))
    
    hand_df <- read_handover(ph)
    gaze_df <- read_gaze(pg)
    
    # Assign trials to gaze
    g_tr <- assign_trials(gaze_df, hand_df)
    
    # Metrics
    sm <- summarise_trial_metrics(g_tr, hand_df)
    
    fi <- sm$face_intervals %>%
        mutate(participant = pid, condition = cond)
    ts <- sm$trial_summary %>%
        mutate(participant = pid, condition = cond)
    
    all_face_intervals[[length(all_face_intervals) + 1]] <- fi
    all_trial_summary[[length(all_trial_summary) + 1]] <- ts
}

face_intervals_all <- bind_rows(all_face_intervals)
trial_summary_all  <- bind_rows(all_trial_summary)

# Theme and colors
condition_levels <- c("static", "dynamic")
condition_palette <- c("static" = "#D62728",  # red
                       "dynamic" = "#17b3b7") # blue

# Enforce condition ordering everywhere
trial_summary_all <- trial_summary_all %>%
    mutate(condition = factor(condition, levels = condition_levels))
face_intervals_all <- face_intervals_all %>%
    mutate(condition = factor(condition, levels = condition_levels))

# Change theme
theme_set(
    theme_bw(base_size = 12) +
        theme(
            panel.grid.major = element_line(color = "grey90", size = 0.25),
            panel.grid.minor = element_blank(),
            strip.background = element_rect(fill = "white", color = "grey40"),
            strip.text = element_text(color = "black"),
            axis.text = element_text(color = "black"),
            axis.title = element_text(color = "black"),
            legend.title = element_text(color = "black"),
            legend.text = element_text(color = "black"),
            plot.title = element_text(color = "black", face = "bold")
        )
)

scale_cond_col <- scale_color_manual(values = condition_palette, drop = FALSE)
scale_cond_fill <- scale_fill_manual(values = condition_palette, drop = FALSE)

# Plot: Within-trial density of robot-face fixations

# Compute x limits
compute_limits <- function(vec, pad_frac = 0.04) {
    v <- vec[is.finite(vec)]
    if (!length(v)) return(c(0, 1))
    rng <- range(v, na.rm = TRUE)
    if (rng[1] == rng[2]) {
        delta <- ifelse(rng[1] == 0, 1, abs(rng[1]) * 0.1)
        return(rng + c(-delta, delta))
    }
    pad <- diff(rng) * pad_frac
    c(rng[1] - pad, rng[2] + pad)
}

xlim_density <- compute_limits(face_intervals_all$rel_mid_s)

# Density plots
p_density <- face_intervals_all %>%
    ggplot(aes(x = rel_mid_s, fill = condition, color = condition)) +
    geom_density(alpha = 0.25) +
    scale_cond_col + scale_cond_fill +
    facet_wrap(~ condition, scales = "fixed", labeller = as_labeller(c(
        "dynamic" = "Adaptive",
        "static"  = "Static"
    ))) +  # lock scales across facets
    coord_cartesian(xlim = xlim_density) +
    xlab("Time within trial (s)") +
    ylab("Density") +
    ggtitle("Robot-Face Gaze Density within Trials") +
    theme(legend.position = "none")

ggsave("figures/robot_face_within_trial_density.png", p_density, width = 10, height = 5, dpi = 300)

# Minima calculation

density_adjust <- 1.0
minima_window <- NULL

# Find the lowest point
find_local_minima_idx <- function(y) {
    n <- length(y)
    if (n < 3) return(integer(0))
    dy <- diff(y)
    which(dy[-1] > 0 & dy[-length(dy)] < 0) + 1
}

# Extract minima (density + time) for each participant
density_minima <- face_intervals_all %>%
    filter(is.finite(rel_mid_s)) %>%
    group_by(participant, condition) %>%
    group_map(.f = function(df, key) {
        v <- df$rel_mid_s
        if (length(v) < 5) return(tibble())
        
        d <- density(v, adjust = density_adjust, na.rm = TRUE)
        
        if (!is.null(minima_window)) {
            keep <- d$x >= minima_window[1] & d$x <= minima_window[2]
            if (!any(keep)) return(tibble())
            x <- d$x[keep]; y <- d$y[keep]
        } else {
            x <- d$x; y <- d$y
        }
        
        mins_idx <- find_local_minima_idx(y)
        if (!length(mins_idx)) return(tibble())
        
        tibble(
            participant = key$participant,
            condition = key$condition,
            x_min_s = x[mins_idx],
            y_min = y[mins_idx]
        ) %>%
            arrange(x_min_s)
    }) %>%
    bind_rows() %>%
    ungroup() %>%
    arrange(condition, participant, x_min_s)

# Output
if (!nrow(density_minima)) {
    message("No local minima detected.")
} else {
    dir.create("figures", showWarnings = FALSE)
    write_csv(density_minima, "figures/robot_face_density_local_minima.csv")
}


# Across-trial trends in robot-face gaze

# Compute x limits
compute_limits <- function(vec, pad_frac = 0.04) {
    v <- vec[is.finite(vec)]
    if (!length(v)) return(c(0, 1))
    rng <- range(v, na.rm = TRUE)
    if (rng[1] == rng[2]) {
        # Expand a flat range a bit to avoid zero-height panels
        delta <- ifelse(rng[1] == 0, 1, abs(rng[1]) * 0.1)
        return(rng + c(-delta, delta))
    }
    pad <- diff(rng) * pad_frac
    c(rng[1] - pad, rng[2] + pad)
}

lims <- list(
    face_fix_count = compute_limits(trial_summary_all$face_fix_count),
    face_total_s   = compute_limits(trial_summary_all$face_total_s),
    face_mean_s    = compute_limits(trial_summary_all$face_mean_s),
    face_prop_of_trial = compute_limits(trial_summary_all$face_prop_of_trial)
)

plot_trial_trend <- function(metric, ylab = metric, title = NULL) {
    ggplot(trial_summary_all,
           aes(x = trial, y = .data[[metric]],
               color = condition,
               group = interaction(participant, condition))) +
        geom_line(alpha = 0.7) +
        geom_point(size = 1.2) +
        geom_smooth(aes(group = condition, color = condition),
                    method = "loess", se = TRUE, size = 1.0, span = 0.75) +
        scale_cond_col +
        facet_wrap(~ condition, scales = "fixed", labeller = as_labeller(c(
            "dynamic" = "Adaptive",
            "static"  = "Static"
        ))) +
        scale_x_continuous(breaks = seq(0, 40, by = 5)) +
        coord_cartesian(ylim = lims[[metric]]) +
        xlab("Trial number") + ylab(ylab) +
        theme(legend.position = "none") +
        ggtitle("Proportion of Trial Spent Fixating Robot-Face")
}

p_prop <- plot_trial_trend("face_prop_of_trial", "Proportion", "Proportion of Trial Spent Fixating Robot-Face")
ggsave("figures/trend_face_prop.png", p_prop, width = 11, height = 5, dpi = 300)

