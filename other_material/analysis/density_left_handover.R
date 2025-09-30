suppressPackageStartupMessages({
    library(tidyverse); library(lubridate); library(janitor); library(glue); library(data.table)
})

# Files
handover_files <- c("handover_data/514_static_handover.csv",
                    "handover_data/667_static_handover.csv",
                    "handover_data/713_static_handover.csv",
                    "handover_data/941_static_handover.csv",
                    "handover_data/565_static_handover.csv",
                    "handover_data/180_dynamic_handover.csv",
                    "handover_data/227_dynamic_handover.csv",
                    "handover_data/288_dynamic_handover.csv",
                    "handover_data/566_dynamic_handover.csv",
                    "handover_data/944_dynamic_handover.csv")

gaze_files <- c("gaze_data/514_static_gaze.csv",
                "gaze_data/667_static_gaze.csv",
                "gaze_data/713_static_gaze.csv",
                "gaze_data/941_static_gaze.csv",
                "gaze_data/565_static_gaze.csv",
                "gaze_data/180_dynamic_gaze.csv",
                "gaze_data/227_dynamic_gaze.csv",
                "gaze_data/288_dynamic_gaze.csv",
                "gaze_data/566_dynamic_gaze.csv",
                "gaze_data/944_dynamic_gaze.csv")

# Group from filename
get_meta_from_path <- function(path) {
    fn <- basename(path)
    id <- stringr::str_extract(fn, "(?<=^|_)\\d{3}(?=_)")
    cond <- dplyr::case_when(
        stringr::str_detect(fn, "dynamic") ~ "dynamic",
        stringr::str_detect(fn, "static")  ~ "static",
        TRUE ~ NA_character_
    )
    tibble(file = path, participant = id, condition = cond)
}

handover_meta <- purrr::map_dfr(handover_files, get_meta_from_path)
gaze_meta     <- purrr::map_dfr(gaze_files,     get_meta_from_path)

meta_pairs <- dplyr::inner_join(handover_meta, gaze_meta, by = c("participant", "condition"),
                                suffix = c("_handover", "_gaze"))

# Functions for reading files
read_handover <- function(path) {
    readr::read_csv(path, show_col_types = FALSE) %>%
        clean_names() %>%
        mutate(initiation = lubridate::ymd_hms(initiation),
               trial = dplyr::row_number())
}

read_gaze <- function(path) {
    readr::read_csv(path, show_col_types = FALSE) %>%
        clean_names() %>%
        mutate(start_time = lubridate::ymd_hms(start_time),
               end_time = start_time + duration/1000)
}

# Assign trial number based on handover data row
assign_trials <- function(gaze_df, hand_df) {
    hand_key <- hand_df %>% arrange(initiation) %>% mutate(next_initiation = dplyr::lead(initiation))
    gdt <- as.data.table(gaze_df); hdt <- as.data.table(hand_key); data.table::setkey(hdt, initiation)
    ans <- hdt[gdt, roll = TRUE, on = .(initiation = start_time)]
    out <- cbind(gaze_df, ans[, .(trial, initiation, next_initiation)])
    dplyr::filter(out, !is.na(trial))
}

# Process data
all_face_intervals <- list()
for (i in seq_len(nrow(meta_pairs))) {
    ph <- meta_pairs$file_handover[i]; pg <- meta_pairs$file_gaze[i]
    pid <- meta_pairs$participant[i]; cond <- meta_pairs$condition[i]
    hand_df <- tryCatch(read_handover(ph), error = function(e) NULL)
    gaze_df <- tryCatch(read_gaze(pg),     error = function(e) NULL)
    if (is.null(hand_df) || is.null(gaze_df)) next
    g_tr <- tryCatch(assign_trials(gaze_df, hand_df), error = function(e) NULL)
    if (is.null(g_tr)) next
    
    hand_key <- hand_df %>%
        arrange(trial) %>%
        transmute(trial, trial_start = initiation)
    
    # Filter fixation target
    dat <- g_tr %>%
        filter(target == "left_handover_location") %>%
        mutate(duration_s = duration/1000,
               mid_time = start_time + duration_s/2) %>%
        left_join(hand_key, by = "trial") %>%
        filter(!is.na(trial_start)) %>%
        mutate(rel_mid_s = as.numeric(mid_time - trial_start, units = "secs"),
               participant = pid,
               condition = cond)
    
    all_face_intervals[[length(all_face_intervals) + 1]] <- dat
}

face_intervals_all <- dplyr::bind_rows(all_face_intervals)
if (nrow(face_intervals_all) == 0) stop("No data for left_handover_location.")

# Theme and colors
condition_levels <- c("static", "dynamic")
condition_palette <- c("static" = "#D62728", "dynamic" = "#1F77B4")
face_intervals_all <- face_intervals_all %>%
    mutate(condition = factor(condition, levels = condition_levels))

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
scale_cond_col  <- scale_color_manual(values = condition_palette, drop = FALSE)
scale_cond_fill <- scale_fill_manual(values = condition_palette, drop = FALSE)

# Compute x limits dynamically
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

# Create density plot for left-handover

dir.create("figures", showWarnings = FALSE)

p_density_left <- face_intervals_all %>%
    ggplot(aes(x = rel_mid_s, fill = condition, color = condition)) +
    geom_density(alpha = 0.25) +
    scale_cond_col + scale_cond_fill +
    facet_wrap(~ condition + participant, scales = "fixed") +
    coord_cartesian(xlim = xlim_density) +
    xlab("Time within trial (s)") +
    ylab("Density") +
    ggtitle("Within-trial timing: left_handover_location")

ggsave("figures/density_within_trial_left_handover_location.png",
       p_density_left, width = 10, height = 7, dpi = 200)

# Calculate time within trial of highest peak
get_highest_peak_mean_x <- function(df, by_facet = TRUE) {
    stopifnot("rel_mid_s" %in% names(df))
    
    if (nrow(df) == 0) return(if (by_facet) tibble() else NA_real_)
    
    find_peak <- function(x) {
        x <- x[is.finite(x)]
        if (!length(x)) return(NA_real_)
        d <- try(stats::density(x, na.rm = TRUE), silent = TRUE)
        if (inherits(d, "try-error") || is.null(d$y) || !length(d$y)) return(NA_real_)
        d$x[which.max(d$y)]
    }
    
    if (by_facet) {
        df %>%
            dplyr::group_by(condition, participant) %>%
            dplyr::summarise(peak_mean_x = find_peak(rel_mid_s), .groups = "drop") %>%
            dplyr::arrange(condition, participant) %>%
            { print(.); . }
    } else {
        val <- find_peak(df$rel_mid_s)
        cat(glue::glue("Overall highest peak mean x: {round(val, 3)} s\n"))
        val
    }
}

# Print density peak time
invisible(get_highest_peak_mean_x(face_intervals_all, by_facet = FALSE))

