# Notebook Guide: what each part of `formula-1.ipynb` does

This guide walks through [formula-1.ipynb](../formula-1.ipynb) in order: what each code cell does, why it is there, and how to read each figure. All numbers come from a full run of the notebook on the local `archive/` data (pandas 2.3.3).

**The project in one paragraph.** We predict whether a driver finishes on the podium (top three) in a Formula 1 race. The prediction is made after qualifying and before the race starts, so nothing that happens during or after the race may be used as an input. The notebook loads the 14 raw tables, checks and cleans them (`clean_df`), answers three data-engineering questions, builds 21 pre-race features (`model_df`), trains and compares five models, and then measures and explains what the selected model relies on.

---

## Section 1: Shared components

These cells hold everything the four members must treat the same way. Later sections use these names and never hard-code the values.

### 1.1 Config

| Name | Value | Meaning |
| :--- | :--- | :--- |
| `RANDOM_SEED` | 42 | Makes random steps repeatable (DEC-001). |
| `TRAIN_MAX_YEAR`, `VAL_YEARS`, `TEST_MIN_YEAR` | 2019, (2020, 2021), 2022 | The split by season (DEC-002). We split by time, not at random, so the model is never trained on seasons later than the ones it is tested on. |
| `EXCLUDE_INDY_500` | `True` | Switch for dropping the Indianapolis 500 races (DEC-003). |
| `SENTINEL_VALUES` | `\N` and empty string | How the CSV files write "missing". |
| `FIGURES_DIR` | `figures/` | Where every plot is saved. |
| `DATASET_DIR` | found automatically | `resolve_dataset_dir()` looks for the folder that contains `results.csv`, first on Kaggle, then in a local `archive/` folder (DEC-006). |

### 1.2 Plot style and `save_fig`

`F1_PALETTE` is the shared set of colours. The `plt.rcParams` block sets font sizes and grid style once, so all figures look alike. `save_fig("name")` saves the current plot as `figures/name.png` at 300 DPI, ready for the report (DEC-007).

### 1.3 Leakage guard

"Leakage" means giving the model information it could not have at prediction time, which makes scores look better than they really are.

- `LEAKAGE_BLACKLIST_COLUMNS`: columns produced during or after the race (finishing position, points, laps, race time, fastest lap, status, and so on). They may never be features.
- `LEAKAGE_PATTERNS`: name patterns that catch renamed versions, such as anything starting with `fastest` or `post_`.
- `TABLE_TEMPORAL_AUDIT`: one line per table saying whether it is safe before the race.
- `assert_leakage_safe(feature_cols)`: give it a list of feature names; it raises an error if any of them is blacklisted. The loop under it is a self-test that confirms the guard rejects five known outcome columns.

### 1.4 Data contract

The contract is the agreed shape of the modeling table (DEC-005).

- `GRAIN = ["raceId", "driverId"]`: one row per driver per race.
- `IDENTIFIER_COLUMNS`: `raceId`, `driverId`, `constructorId`, `date`, `year`. They identify a row and are not features.
- `TARGET_COLUMN = "podium"`: 1 for a top-three finish, 0 otherwise.
- `FEATURE_GROUPS`: the planned feature names, grouped. The ablation study and the explainability section loop over this dict.
- `validate_data_contract(df)`: checks that the grain is unique, the identifiers have no missing values, the target is only 0 or 1, and (if you pass `feature_cols`) that the features pass the leakage guard.

### 1.5 Decision log (markdown)

A copy of decisions DEC-001 to DEC-007 and a short list of which tables are safe. The full log, DEC-001 to DEC-032, is in [decision_log.md](decision_log.md).

### 1.6 Raw data loader

`load_raw_datasets()` reads every CSV in the dataset folder into a dictionary, `raw_dataframes`, keyed by table name. `\N` is read as a missing value. `raw_dataframes` is never changed afterwards; all cleaning is done on copies, so we can always compare before and after.

---

## Section 2: Step 1, the data audit

### Task 1: Raw table inventory

| Cell | What it does |
| :--- | :--- |
| 1.1 | Asserts that exactly the 14 expected tables loaded and none is empty. Builds `inventory_summary_df`: rows, columns, memory, missing cells and column types per table. |
| 1.2 | Prints `.info()` for every table: each column's type and how many values are present. |
| 1.3 | Prints summary statistics for `results` and `qualifying`, the two tables the pipeline is built on. |
| 1.4 | Builds two helper tables used later (`raw_with_year`: raw results plus the season; `quali_with_year`: raw qualifying plus the season) and prints key facts. |

Key facts from Task 1:

- 701,433 rows in total. `lap_times` alone is 84% of them, and it is forbidden as a feature because it is recorded during the race.
- `results` has 26,759 rows over 1,125 races, 1950–2024. The raw podium rate is 12.69%.
- `positionText` holds the finishing position, or a letter when the driver was not classified: `R` retired, `F` failed to qualify, `W` withdrew, `D` disqualified, `N` not classified, `E` excluded.
- `qualifying` only has rows from 1994. `q2` is missing in 44% of rows and `q3` in 65%, which is expected: a driver knocked out in an earlier session has no later time.

### Task 2: Keys and referential integrity

| Cell | What it does |
| :--- | :--- |
| 2.1 | For each table, checks that its key (for example `raceId` in `races`, or `raceId + driverId + lap` in `lap_times`) has no missing and no repeated values. All 16 keys pass. |
| 2.2 | Measures the one known exception: `results` has repeated `(raceId, driverId)` pairs. |
| 2.3 | For each of the 22 foreign keys, counts "orphans": rows whose key points to a parent row that does not exist (for example a result whose `driverId` is not in `drivers`). All 22 have zero orphans. |

Why `results` has duplicates: in the 1950s a driver could take over a teammate's car mid-race, and each car they drove got its own row. This affects 176 rows in 85 driver-race pairs; 91 of those rows are surplus. They are removed in Task 6.

### Task 3: "Before" plots

Six plots of the raw data, saved as `figures/before_eda_*.png`.

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `before_eda_missingness_heatmap` | Bar chart of the share of missing values per column, coloured by table. (The file is named "heatmap" for historical reasons.) | The emptiest columns are session times in `races` (over 90%), which only exist for recent seasons. In `results`, race time and fastest-lap columns are about 70% empty: they are outcome columns, missing for anyone who did not finish, and fastest laps were only recorded from 2004. |
| `before_eda_rows_per_season` | Number of `results` rows per season. | Grows from 160 rows in 1950 to a peak of 620 in 1989, when far more cars entered than could start. Modern seasons have about 400–480 rows. |
| `before_eda_entrants_per_race` | Box plot of rows per race, grouped by decade. The dashed line is today's 20-car grid. | Older decades have large and very variable fields (up to 55 rows in one 1950s race), because the raw table also lists drivers who never started. From the 2000s the boxes sit at about 20. |
| `before_eda_qualifying_coverage` | Top: rows per season in `results` and in `qualifying`. Bottom: qualifying rows as a share of results rows. Dashed lines mark the first qualifying rows (1994) and the Q1/Q2/Q3 knockout format (2006). | There is no qualifying data before 1994. Coverage then drops to between 6% and 59% in 1996–2002 and is complete only from 2003. Any feature built on qualifying needs a fallback for the earlier seasons. |
| `before_eda_podium_base_rate` | Share of rows that are podium finishes, per season. Dotted line: all raw rows (12.69%). Dashed line: 15%, which is 3 of 20 cars. | The rate depends on field size. It falls to 7.74% in 1989, when the entry lists were longest, and sits near 15% in the modern era. |
| `before_eda_duplicate_distribution` | Number of rows involved in shared drives, per season. | Almost all are from 1953–1956 (120 of 176 rows). The last case is in 1978. |

---

## Section 3: Step 2, cleaning

### Task 4: Types and sentinels

| Cell | What it does |
| :--- | :--- |
| 4.1 | Defines `lap_time_to_seconds()`, which turns `"1:24.312"` into `84.312`. Copies every raw table into `cleaned_dataframes`. Converts `races.date`, `drivers.dob` and the session dates to real dates, and converts `q1`, `q2`, `q3` and pit-stop durations to seconds. |
| 4.2 | Checks: no time was lost in parsing (the count of missing values is the same before and after), no table still contains the text `\N`, and the raw tables were not changed. Shows a small before/after table of the converted columns. |

Rows with a missing `q2` or `q3` are kept on purpose (see Task 1).

### Task 5: Scope filtering and non-starters

A working table, `results_work`, is built from the typed results plus the season, race name and status text. Three rules are applied to it in order, and `cleaning_ledger` records how many rows are left after each.

| Cell | Rule | Effect |
| :--- | :--- | ---: |
| 5.1 | **DEC-003.** Drop the Indianapolis 500 races of 1950–1960. They counted for the championship but were run to different rules, on an oval, with a different field of drivers. | 11 races, 405 rows removed |
| 5.2 | **DEC-009.** Drop non-starters: the driver completed zero laps **and** is either labelled as failed to qualify / not pre-qualified / withdrawn, or had no grid slot. | 1,715 rows removed |
| 5.3 | **DEC-010.** Every `grid = 0` row still left is a real pit-lane start. Set `pit_start = 1` and move `grid` to one place behind the last car on that race's grid. | 72 rows recoded, none removed |

Why DEC-009 needs "zero laps": the label alone is unreliable. 1,724 rows carry a non-starter label, but 24 of them completed racing laps and are kept. The check in the cell confirms that no podium finisher is removed.

Why DEC-010 recodes `grid`: left as 0, a model would read a pit-lane start as better than pole position (grid 1). The `pit_start` flag keeps these rows distinguishable.

### Task 6: Shared-drive deduplication

**DEC-008.** Where a driver still has more than one row in a race, keep the car they started in, break ties by the best finishing position, and drop the rest. After Task 5 there are 125 such rows in 61 groups (1950–1964); 64 rows are removed. In practice the finishing position decides every group. The cell ends by confirming that `(raceId, driverId)` is now unique: 24,575 rows.

### Task 7: Base table and target

| Cell | What it does |
| :--- | :--- |
| 7.1 | Makes two side tables safe to merge: `qualifying_clean` (its `position` column is renamed `quali_position`) and `sprint_clean` (every column gets a `sprint_` prefix). Without this their column names would clash with the blacklisted `results` columns. Then joins the cleaned results to `races` and `circuits`, adds `podium = (positionOrder <= 3)`, and runs `validate_data_contract()`. The result is `clean_df`. |
| 7.2 | Shows the target in each split, and counts podium rows per race. |

| Split | Rows | Races | Podiums | Podium rate |
| :--- | ---: | ---: | ---: | ---: |
| Train (≤ 2019) | 22,448 | 1,007 | 3,038 | 13.53% |
| Validation (2020–2021) | 775 | 39 | 117 | 15.10% |
| Test (≥ 2022) | 1,352 | 68 | 204 | 15.09% |

Fifteen races have four or five podium rows instead of three, because two drivers shared a car that finished on the podium and both were credited. They are kept on purpose.

`clean_df` still contains the race-outcome columns. The analytics questions need them, but they stay blacklisted as model features.

### Task 8: "After" plots

The same views as Task 3, with raw and cleaned data side by side, saved as `figures/after_eda_*.png`.

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `after_eda_row_count_waterfall` | One bar per cleaning stage. Dark is what remains, red is what that stage removed. The axis starts at 22,000 so the removed parts are visible. | 26,759 → 26,354 → 24,639 → 24,575. Non-starter removal is by far the largest step. In total 8.2% of raw rows are removed. |
| `after_eda_entrants_per_race` | Box plots of rows per race by decade, grey before and red after. | The largest "field" falls from 55 entries to 34 starters. The 1970s–1990s boxes drop the most, because those entry lists were padded with drivers who failed to qualify. From 2000 the two boxes are almost the same. |
| `after_eda_missingness` | Missing values in the `results` columns, grey before and red after. | Missing finishing positions fall from 40.9% to 36.6%, because non-starters never had a position. The rest barely moves: those gaps are real (retired drivers have no race time; fastest laps exist only from 2004). |
| `after_eda_podium_base_rate` | Podium rate per season, dashed grey before and red after. Shaded bands mark the validation and test seasons. | Overall 12.69% → 13.67%. The rate rises most in the 1950s (1956: +4.0 points) and in the crowded 1970s–1990s. From the mid-1990s the lines coincide, so cleaning does not distort the modern seasons used for validation and testing. |
| `after_eda_qualifying_coverage` | Share of rows that have a matching qualifying record, per season, before and after. | Cleaning hardly changes it. The gap in 1996–2002 comes from the source data, not from our cleaning. From 2003 only 21 cleaned rows lack a qualifying record. |

The last cell (8.6) lists the final column types and runs the closing checks: numeric columns are numeric, `date` is a date, no `\N` text remains, and the raw results were not changed.

### What the notebook hands over

| Object | Contents |
| :--- | :--- |
| `clean_df` | 24,575 rows, one per driver per race, with race and circuit context, `pit_start` and `podium`. |
| `qualifying_clean` | Qualifying with `quali_position` and `q1`–`q3` in seconds. |
| `sprint_clean` | Sprint results with every non-key column prefixed `sprint_`. |
| `cleaned_dataframes` | Typed copies of all 14 tables; `results` is the cleaned version. |

---

## Section 4: Step 3, the data-engineering questions

Three questions answered from `clean_df` joined to other tables. Each one ends with a markdown cell holding the answer, the joins, and notes on grain, missing values and the pre-race cutoff. These are descriptive analyses: `podium` and `status` are the outcomes being measured and stay blacklisted as model features.

The first cell imports `scipy` and `statsmodels` and defines `rate_table()`, which returns, per group, the number of rows, the number of events, the rate and its Wilson 95% interval.

### Task 9: Q1, front-row conversion by circuit

| Cell | What it does |
| :--- | :--- |
| 9.1 | Joins `clean_df` (2003 onward) to `qualifying_clean` and flags a front-row start two ways: `grid` 1–2 and `quali_position` 1–2. Counts how often the two disagree. |
| 9.2 | Podium rate per circuit and era under each definition, keeps circuits with at least 10 front-row starts in both eras, and compares the two eras' rankings with Spearman's ρ. |
| 9.3 | Dumbbell chart, `de_q1_front_row_conversion`. |

**Answer.** Front-row starts reach the podium more often in 2014–2024 (76.2%) than in 2003–2013 (68.3%). Monaco, Suzuka and Yas Marina convert most often in the hybrid era. The ranking is only loosely preserved (ρ = 0.36 on grid, 0.54 on qualifying). Grid penalties moved 2.3% of top-two qualifiers off the front row before 2014 and 6.0% after.

**How to read the chart.** One row per circuit; the grey dot is 2003–2013 and the red dot is 2014–2024. A long bar to the right means the circuit converts much more often in the hybrid era. Each dot rests on 10 to 24 starts, so small gaps are noise.

Why 2003 (DEC-011): the qualifying file is missing whole races before then, so earlier seasons cannot support the qualifying-based definition.

### Task 10: Q2, home advantage

| Cell | What it does |
| :--- | :--- |
| 10.1 | Maps `drivers.nationality` to home countries and sets `is_home` when the circuit is in one of them (DEC-012). |
| 10.2 | Home and away podium rates inside each grid bucket (1, 2–3, 4–6, 7–10, 11+). |
| 10.3 | Cochran–Mantel–Haenszel test and logistic regression `podium ~ is_home + C(grid_bucket)`, plus three robustness checks. |
| 10.4 | Grouped bar chart, `de_q2_home_advantage`. |

**Answer.** No detectable home advantage once grid position is held fixed: pooled odds ratio 0.95 (95% CI 0.80 to 1.13, p = 0.61). The raw home rate is lower (11.92% vs. 13.82%) only because home drivers start further back on average.

**How to read the chart.** Each pair of bars compares drivers who started from similar positions. The black lines are 95% intervals; in every bucket the home and away intervals overlap.

### Task 11: Q3, mechanical retirements

| Cell | What it does |
| :--- | :--- |
| 11.1 | Maps all 139 statuses to finished, mechanical, accident/driver or regulatory/other (DEC-013), and asserts none is left unmapped. |
| 11.2 | Mechanical retirements per race start, per constructor and era, for constructors with at least 40 starts in the era. |
| 11.3 | Ranked bar chart per era, `de_q3_mechanical_retirements`. |
| 11.4 | Merges renamed teams (DEC-014) and draws a slope chart of the same teams across both eras, `de_q3_mechanical_retirements_lineage`. |
| 11.5 | Sensitivity run: counts the generic `Retired` label as mechanical and checks whether the ranking moves. |

**Answer.** 2014–2021: Lotus F1 (18.7%), Toro Rosso (16.1%), Renault (14.1%). 2022–2024: Alfa Romeo (12.5%), Alpine (10.4%), AlphaTauri (8.0%). The field-wide rate fell from 9.43% to 5.92% of starts.

**How to read the charts.** In the bar chart the label gives the rate and the counts behind it (retirements / starts); the grey line is the 95% interval, which is wide for teams with few starts. In the slope chart a line going down means the team became more reliable.

---

## Section 5: Step 4, feature engineering

This section turns `clean_df` into `model_df`, the table the models are trained on: 24,575 rows, the 5 identifiers, `podium` and 21 features in 6 groups. Missing values are left as `NaN` on purpose; filling them is Step 5.

### Task 12: Feature construction

| Cell | What it does |
| :--- | :--- |
| 12.1 | Builds `feature_base` from `clean_df`, sorted by date, and checks that no driver has two rows on one date (which is what makes "shift by one row" mean "strictly earlier"). |
| 12.2 | Grid: `front_row`, and `teammate_grid_diff` (the driver's slot minus the average slot of the team's other cars). |
| 12.3 | Qualifying: `quali_position`, `gap_to_pole`, `q3_reached`, `missing_quali_flag` (DEC-017). |
| 12.4 | Driver form, constructor form, and the driver's record at the circuit. Every one uses `shift(1)` before the rolling or expanding window. |
| 12.5 | Standings entering the race, taken from the standings table at the previous round. |
| 12.6 | Context: `field_size` and `is_home_race` (the Q2 mapping). |
| 12.7 | Shows that the training seasons contain no sprint and removes the sprint group (DEC-016). |
| 12.8 | `build_feature_table()` chains the functions above and produces `model_df`; the data contract and the leakage guard are run on it. |
| 12.9 | `FEATURE_REGISTRY`: for each feature, its group, source tables, definition and why it is known before the race. This table goes into the report. |

Two ideas to be able to explain:

- **`shift(1)`.** A rolling average over a driver's rows would include the current race. Shifting by one row first means the window for race *t* ends at race *t − 1*.
- **Points as shares (DEC-015).** A win gave 9 or 10 points for most of the training seasons and 25 from 2010. Dividing by the points awarded (or by the leader's points) keeps the feature on one scale across eras.

### Task 13: Leakage tests

| Cell | What it does |
| :--- | :--- |
| 13.1 | Recomputes six history features for 300 random rows the slow way, using only rows with an earlier date, and asserts they match `model_df`. |
| 13.2 | For 20 random races, scrambles every outcome from that race onward, rebuilds the table, and asserts that the race's 21 features did not change. A control feature built without `shift(1)` is flagged in 20 of 20 races, which shows the test can detect leakage. |

### Task 14: Feature validation

All views that relate a feature to the target use the training seasons only.

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `feat_missingness_by_decade` | Share of missing values per feature and decade. | Qualifying features are empty before the 1990s and complete from the 2010s. The standings ranks are missing at round 1. The circuit rate is missing on a driver's first visit. |
| `feat_podium_rate_by_grid` | Podium rate for each grid position, with 95% intervals. | Falls steeply: 63% from pole, 35% from fourth, 6% from tenth, under 1% from twentieth. The dashed line is the training base rate. |
| `feat_correlation_matrix` | Spearman correlation between all features and the target. | Dark cells off the diagonal mark features that carry the same information, such as `quali_position` and `grid` (0.98). The bottom row is each feature's correlation with `podium`. |
| `feat_distributions_by_class` | Box plots of each continuous feature for podium and non-podium rows. | The further apart the two boxes, the more the feature separates the classes. `round` and `field_size` barely differ. |
| `feat_univariate_auc` | ROC-AUC of each feature used alone, coloured by group. | 0.5 is no signal. Qualifying and grid are near 0.9; form and standings near 0.8; `pit_start`, `is_home_race`, `round` and `missing_quali_flag` are at 0.5. |

Cell 14.6 compares rolling windows of 3, 5 and 10 races (DEC-018).

No feature is dropped at this stage. The weak ones are kept so the ablation in Step 7 can measure them properly.

---

## Section 6: Step 5, split and preprocessing

This section splits `model_df` by season, builds the preprocessing pipeline and runs the experiments that decide how it is used. Every comparison is scored on the validation seasons (2020–2021). The test seasons are transformed at the end but never scored here.

### Task 15: Temporal split

| Cell | What it does |
| :--- | :--- |
| 15.1 | `split_by_season()` returns train (up to 2019), validation (2020–2021) and test (2022 on), and asserts that the three do not overlap in time. |
| 15.2 | Shows how many validation and test rows belong to a driver or constructor never seen in training. This is why the identifiers are not one-hot encoded (DEC-020). |

### Task 16: Pipeline and scoring helpers

| Cell | What it does |
| :--- | :--- |
| 16.1 | `make_preprocessor()` builds the pipeline: grid fallback for a missing qualifying position, median imputation and standard scaling for the 16 continuous features, and a constant 0 for missing flags. `make_reference_model()` is the logistic regression used to score the experiments. |
| 16.2 | `validation_probabilities()` fits a preprocessor and model and predicts the validation seasons. `compare_on_validation()` reports ROC-AUC and PR-AUC per variant and the PR-AUC difference to a reference, with a 95% interval from resampling whole races 500 times. |

Terms to be able to explain:

- **Imputation** fills a missing value. Here the fill is the median of the training rows.
- **Standard scaling** subtracts the training mean and divides by the training standard deviation, so every continuous feature is on the same scale.
- **Fitting on train only** means the medians, means and standard deviations are computed from the training seasons and then applied unchanged to validation and test.
- **The bootstrap interval** says how much a difference could move if the validation races had been a slightly different set. If it includes 0, the difference is not distinguishable from noise.

### Task 17: Training-window experiment (DEC-019)

Trains on all seasons, from 1994, from 2003 and from 2006, with two ways of filling missing qualifying values, plus a gradient-boosting check.

| Training window | Train rows | Logistic, grid fallback (val PR-AUC) | Gradient boosting (val PR-AUC) |
| :--- | ---: | ---: | ---: |
| All seasons | 22,448 | 0.728 | 0.704 |
| From 1994 | 10,091 | 0.720 | 0.704 |
| From 2003 | 6,782 | 0.725 | 0.693 |
| From 2006 | 5,743 | 0.729 | 0.665 |

**Decision.** Train on all seasons and fill a missing qualifying position from the grid slot. The window makes no real difference to the logistic regression, and less data hurts the gradient-boosting model. Figure: `prep_training_window` (note its y-axis is zoomed in; the logistic lines differ by less than 0.01).

### Task 18: Distributions before and after each transformation

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `prep_distributions_by_stage` | Four features, each raw, after imputation and after scaling; grey is train, orange is validation, teal is test. | Scaling changes the axis but not the shape. Imputation adds a spike at the training median, tall for `gap_to_pole`. Validation and test have no tail beyond 20 cars. |
| `prep_distribution_shift` | The mean of each scaled feature in validation and test. 0 is the training mean. | `field_size` is almost one standard deviation lower than in training (20-car grids), and `round` is higher (longer seasons). |

### Task 19: Preprocessing-order experiments (DEC-021)

| Experiment | Variants | Validation PR-AUC difference |
| :--- | :--- | :--- |
| 1 | Preprocessor fitted on train only vs. on all rows | 0.0000 (95% interval −0.0005 to +0.0003) |
| 2 | Impute → scale vs. scale → impute | −0.0001 (95% interval −0.0006 to +0.0001) |

Neither changes the score here, and each cell shows why. In experiment 1 the validation and test seasons are only 8.7% of the rows, so the learned statistics barely move. In experiment 2 the scaler does learn a different standard deviation (1.57 vs. 2.57 for `gap_to_pole`), but a logistic regression adjusts its coefficient to compensate. Train-only fitting and impute → scale are kept because they are correct by construction, not because they score higher.

### Task 20: Final matrices

Fits the final preprocessor on the training rows and produces `X_train_prep`, `X_val_prep` and `X_test_prep` (no missing values), alongside the raw `X_train`, `X_val`, `X_test` and the targets `y_train`, `y_val`, `y_test`.

---

## Section 7: Step 6, modeling

Five ways of predicting `podium` are trained on the same rows and the same 21 features and then compared. Three rules hold throughout: every model is fitted on the training seasons only, every choice is made on the validation seasons, and the test seasons are scored once, in Task 28.

### Task 21: Evaluation protocol (DEC-022)

| Cell | What it does |
| :--- | :--- |
| 21.1 | `ranking_metrics()` (ROC-AUC, PR-AUC), `decision_metrics()` (F1, precision, recall), `best_f1_threshold()` and `top3_per_race()`. |
| 21.2 | `register_model()` adds a fitted model to `PREDICTORS`. `compare_models()` gives each PR-AUC a 95% interval by resampling whole races 500 times. `random_search()` tries random hyperparameter settings and ranks them by validation PR-AUC. |

Terms to be able to explain:

- **PR-AUC** (the main metric) measures how well a model ranks the few podium rows above the many non-podium rows, without needing a threshold. With about 15% podiums it is more informative than ROC-AUC, which also rewards ranking the easy back-of-grid rows.
- **A threshold** turns a score into a yes or no. **F1** balances precision (how many predicted podiums were real) and recall (how many real podiums were found).

### Tasks 22 to 25: the five models

| Task | Model | Input | Tuning | Validation PR-AUC |
| :--- | :--- | :--- | :--- | ---: |
| 22 | Grid ≤ 3 rule (DEC-023) | `grid` only | None | 0.648 |
| 22 | Logistic regression | Preprocessed features | None (`C` from 0.01 to 100 gives 0.727 to 0.728) | 0.728 |
| 23 | Random forest (DEC-025) | Preprocessed features | 20 random configurations; best has depth 4 | 0.739 |
| 24 | LightGBM (DEC-024, DEC-025) | Raw features, missing values included | 40 random configurations; best has 100 trees of 8 leaves | 0.743 |
| 25 | Neural network (DEC-026) | Preprocessed features | 8 architectures; best is 64 → 32 units, dropout 0.2 | 0.738 |

Points to be able to explain:

- **Training scores are lower than validation scores for every model** (PR-AUC 0.50 to 0.60). The training seasons run from 1950, have a lower podium rate and mostly lack qualifying data, so they are harder to predict. It is not a sign of a problem.
- **Untuned complex models are worse than the logistic regression.** The untuned forest scores 1.000 on training and 0.683 on validation (overfitting); the untuned LightGBM scores 0.707.
- **The search matters more than the model.** The 20 forest configurations span 0.666 to 0.739, while the best one is only 0.011 above the logistic regression.
- **Early stopping** (network) ends training when validation PR-AUC has not improved for 10 epochs and keeps the best epoch. Five seeds of the chosen network give 0.733 to 0.742, as much spread as between architectures.

Figure: `model_nn_training_history` shows the training and validation loss per epoch. Both curves are still improving slowly when training stops, so the network is not overfitting.

### Task 26: Class weighting (DEC-027)

Each model is refitted without class weights. The ranking does not change measurably (every interval includes zero), but the output does: with weights the average predicted probability is 0.30 to 0.33, twice the true podium rate of 0.151. **The model output is therefore a score, not a calibrated probability.**

### Task 27: Thresholds and model choice (DEC-028, DEC-029)

- Tuned thresholds: 0.64 (logistic regression), 0.74 (forest), 0.74 (LightGBM), 0.82 (network). They sit above 0.5 because of the class weights.
- Validation F1 at those thresholds is 0.709 to 0.721, against 0.695 for the grid rule.
- Figure `model_threshold_f1`: F1 against the threshold. Each curve is nearly flat from 0.6 to 0.85, so the exact threshold is weakly determined.
- **LightGBM is carried forward** because it has the highest validation PR-AUC, the rule fixed beforehand. None of the three tuned models is distinguishable from the logistic regression on validation.

### Task 28: Final evaluation on the test seasons (DEC-030)

| Model | Validation PR-AUC | Test PR-AUC | Test difference to logistic regression (95% interval) |
| :--- | ---: | ---: | :--- |
| Grid ≤ 3 rule | 0.648 | 0.647 | −0.064 (−0.117 to −0.010) |
| Logistic regression | 0.728 | 0.711 | reference |
| Random forest | 0.739 | 0.710 | −0.002 (−0.027 to +0.023) |
| LightGBM | 0.743 | 0.709 | −0.002 (−0.029 to +0.022) |
| Neural network | 0.738 | 0.701 | −0.011 (−0.035 to +0.015) |

What to take from it:

- **The features are worth about 0.06 PR-AUC over the grid rule.** Model complexity adds nothing measurable: the untuned logistic regression is level with the tuned models on test.
- **Tuning on 39 validation races flattered the tuned models.** They lose 0.030 to 0.037 from validation to test; the logistic regression loses 0.017.
- **The thresholds are too low for the test seasons:** 3.3 to 4.6 predicted podiums per race. Test F1 is 0.662 to 0.689, against 0.649 for the grid rule.
- **Top 3 per race gets about two of the three places right, the same as the grid rule.**

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `model_pr_curves` | Precision against recall on validation and test, one line per model. | A line further to the top right is better. The dot on each line is the model at its tuned threshold; the cross is the grid rule. |
| `model_comparison` | PR-AUC and F1 per model on train, validation and test. | The four learned models are level; the grid rule is lower on PR-AUC. |
| `model_confusion_matrix` | LightGBM on test at its threshold and with top 3 per race. | At the threshold: 157 podiums found, 47 missed, 95 false alarms. |

---

## Section 8: Step 7, ablation

The selected model (LightGBM) is retrained with part of the features removed, to measure what each feature group contributes. Only the columns change: same hyperparameters, same training rows, no retuning. Validation and test are both reported, and nothing is chosen from either (DEC-031).

### Task 29: Ablation protocol

| Cell | What it does |
| :--- | :--- |
| 29.1 | `ablation_scores(columns)` retrains LightGBM on a list of columns. `ablation_table()` compares feature sets with the full model: PR-AUC, the difference `Δ`, its 95% race-bootstrap interval, and `Δ` averaged over 10 seeds. `FEATURE_BLOCKS` groups the overlapping feature groups. |

**Why a seed average.** The chosen LightGBM gives each tree a random 70% of the features. The seed alone moves PR-AUC by about 0.006 (0.738 to 0.745 on validation over 10 seeds), so part of any single difference is chance.

### Task 30: Leave one group out

Each of the six groups is removed in turn. **No group is significant: every 95% interval includes zero on both splits.** The largest drops are qualifying on validation (−0.019) and grid on test (−0.019); context is 0.000.

This does not mean the features are useless. Leave-one-out measures what a group adds *on top of all the others*, and the groups overlap: grid and qualifying both say where the car starts; driver form, constructor form and standings all say how the driver and team have been doing.

Figure `ablation_leave_one_group_out`: one pair of bars per removed group (orange validation, teal test), with the 95% interval as a black line. A bar to the left means the model got worse. Every black line crosses zero.

### Task 31: Groups that overlap

| Removed block | Features | Validation Δ (95% interval) | Test Δ (95% interval) |
| :--- | ---: | :--- | :--- |
| Starting position (grid + qualifying) | 8 | −0.089 (−0.145 to −0.034) | −0.123 (−0.181 to −0.072) |
| Past results (driver form + constructor form + standings) | 9 | −0.061 (−0.100 to −0.021) | −0.042 (−0.076 to −0.007) |
| Context | 4 | −0.000 (−0.009 to +0.006) | +0.001 (−0.005 to +0.006) |

What to take from it:

- **The halves of a block are substitutes.** Removing grid or qualifying alone costs at most 0.02; removing both costs 0.09 to 0.12.
- **Starting position is the larger block.** Alone it scores 0.669 on validation and 0.665 on test, about 0.02 above the grid rule.
- **Past results add 0.04 to 0.06 on top.** This is the gain Step 6 found between the grid rule and the learned models.
- **Context can be dropped at no cost.** It is kept because the model was fixed in Step 6 before the test seasons were scored (DEC-031).

Figure `ablation_blocks_and_alone`: on the left, the change in PR-AUC when a block is removed; on the right, the PR-AUC of a model trained on one group or block alone. The dashed lines are the full model and the dotted line is the grid rule.

---

## Section 9: Step 8, explainable AI

This section explains how the fitted LightGBM arrives at its scores. Nothing is retrained and everything is computed on the validation seasons (DEC-032).

### Task 32: Permutation importance

| Cell | What it does |
| :--- | :--- |
| 32.1 | `permutation_drop()` shuffles a feature (or all columns of a group or block together) across the validation rows 50 times and reports the mean drop in PR-AUC with a 95% range. |
| 32.2 | Figure `xai_permutation_importance`. |

- **`grid` alone costs 0.238** (0.155 to 0.310). No other single feature is clearly above zero.
- **`quali_position` costs 0.000**, although it is nearly the same number as `grid`: the model reads the starting position from `grid`.
- **Blocks:** starting position 0.394, past results 0.160, context 0.000.
- **Single-feature importances do not add up:** they sum to 0.318, while shuffling everything costs 0.587. A feature with a substitute is understated.

### Task 33: SHAP values (global)

| Cell | What it does |
| :--- | :--- |
| 33.1 | `shap.TreeExplainer(lgbm_model)` on `X_val`, with an assertion that base value + contributions = model output for every row. `shap_importance`: mean \|SHAP\| per feature. `UNUSED_FEATURES`: features in no tree. |
| 33.2 | Figure `xai_shap_beeswarm`. |
| 33.3 | Figure `xai_shap_dependence`, and the median SHAP value of `grid` per grid slot. |
| 33.4 | `importance_views`: SHAP share, permutation drop and retraining drop (Step 7) per group and block. |

Terms to be able to explain:

- **A SHAP value** is one feature's contribution to one prediction. The base value plus the 21 SHAP values of a row equals the model output for that row.
- **The unit is log-odds**, the model output before it is squashed into a 0-to-1 score. The base value is −1.088 (a score of 0.25) and the decision threshold of 0.739 is +1.04.

| Figure | What it shows | How to read it |
| :--- | :--- | :--- |
| `xai_shap_beeswarm` | One dot per validation row and feature. Position is the SHAP value; colour is the feature value (red high, blue low). | Features are sorted by importance. For `grid`, blue dots (front of the grid) are far to the right: a low grid number raises the score. |
| `xai_shap_dependence` | SHAP value against feature value for the four most important features. | `grid` is a staircase: about +1.6 for slots 1 to 3, zero between slots 9 and 10, −1.03 from slot 15 back. The form features jump once and then stay flat. |

- **`grid` has 41% of all SHAP magnitude**, then `constructor_rolling_points_5` (13%), `driver_rolling_podium_rate_5` (8%) and `driver_career_podium_rate` (8%).
- **Four features are never used:** `pit_start`, `missing_quali_flag`, `is_home_race`, `circuit_historical_podium_rate`.
- **`q3_reached` must not be read literally.** Its SHAP value is about −0.1 whether or not Q3 was reached, because only 25% of training rows have a value for it.

| Block | SHAP share | Permutation drop | Retraining drop (Step 7) |
| :--- | ---: | ---: | ---: |
| Starting position | 55% | 0.394 | 0.089 |
| Past results | 44% | 0.160 | 0.061 |
| Context | 0.6% | 0.000 | 0.000 |

The three agree on the order and differ in size because they ask different questions. Permutation scrambles a block for the *fitted* model, which still trusts it. Retraining gives a *new* model the chance to use what is left.

### Task 34: Two surprising results (SHAP waterfalls)

Two validation rows are chosen by rule: the podium finisher with the lowest score, and the pole-sitter off the podium with the highest score. Both come from the 2020 Italian Grand Prix.

| Case | Score | Result | Largest contributions |
| :--- | ---: | :--- | :--- |
| Pierre Gasly (AlphaTauri), grid 10 | 0.111 | Won | All negative: team's recent points −0.17, grid −0.17, no recent podium −0.12, career podium rate −0.12 |
| Lewis Hamilton (Mercedes), pole | 0.914 | Seventh | All positive: grid +1.65, team's recent points +0.33, five podiums in five races +0.27 |

Figures `xai_shap_waterfall_unexpected_podium` and `xai_shap_waterfall_pole_sitter_off_the_podium`: read from the bottom. The plot starts at the base value, each bar adds one feature's contribution, and the top is the model output for that row.

**The point of the two cases:** the model did not misread its inputs. Both results were decided during the race, and that information does not exist before the start. Errors of this kind set a limit on any pre-race model.

### Task 35: LIME on the same two cases

LIME creates 5,000 artificial rows around the row of interest, scores them with the model and fits a small linear model to those scores. Its weights are the explanation, in units of the model score. The background is the 4,027 training rows with no missing feature (2006–2019), because LIME cannot take a missing value.

| | Gasly | Hamilton |
| :--- | ---: | ---: |
| Fit of LIME's linear model (R²) | 0.05 | 0.83 |
| LIME's top feature | `pit_start = 0` | `grid <= 5` |
| SHAP value of that feature | 0 (never used) | +1.65 |
| Rank correlation with SHAP | 0.47 | 0.89 |
| Different top features across 5 seeds | 3 | 1 |

- **Hamilton:** LIME agrees with SHAP and is stable.
- **Gasly:** LIME fails. Its top feature is one the model never uses, and it changes from seed to seed. `pit_start` is 1 in only 7 of the 4,027 background rows, so its weight is chance.
- **SHAP is the method to rely on:** exact for trees, adds up to the prediction, and identical between runs. Quote LIME only with its R².

### What the explanations do not say

- **Importance is not causation.** `grid` is important because it summarises how fast the car and driver are that weekend. Putting a slow car on pole would not make it a podium contender.
- **Credit between overlapping features is arbitrary.** Quote importance per block, not per feature.
- **The explanations are of the weighted score on 2020–2021**, not calibrated probabilities and not a statement about other seasons.

---

## Where the notebook stands

Steps 1 to 8 of the plan (Tasks 1–35) are in the notebook. Steps 9 and 10 are left; the deadline is 18 October, 11:59 PM.

| Step | Owner | What is left |
| :--- | :--- | :--- |
| 9 | M4 | `predict_podium(raceId, driverId, grid, quali_info=None)`: build the pre-race features for one driver, run the fitted LightGBM, return the score and the yes/no prediction. Show it on a complete record and on one with missing qualifying times. |
| 10 | All | Notebook section on limitations and future work, a full Run All on Kaggle, the report PDF, and the rehearsal on 17 October. |

**Open items outside the notebook (M1's role in [milestone_1_plan.md](milestone_1_plan.md))**

| Item | Status |
| :--- | :--- |
| Team approval of the decisions still marked "Proposed" in [decision_log.md](decision_log.md) | **Open.** DEC-009 and DEC-010 matter most: changing either changes the row counts everything else is built on. |
| Repo setup: `requirements.txt`, README, `.gitignore` | Not done |
| Kaggle setup and a full Run All there | Not done. The Kaggle dataset may be a newer version, which would shift the row counts. |
| Remove the `d:/GUC/...` fallback in the config cell and the `file:///d:/` links in [Step 1,2 plan.md](Step%201,2%20plan.md) and [cleaning_notes.md](cleaning_notes.md) | Not done |
| Final report assembly (Step 10) | Not started |

**Things to carry into Steps 9 and 10**

- **The model output is a score, not a probability.** With class weights it is about twice the true podium rate (Task 26). Step 9 must report it as a score or recalibrate it on validation.
- **The model takes the raw features.** LightGBM needs no imputer or scaler, and a missing qualifying value can be passed as `NaN`. It expects all 21 columns in the order of `FEATURE_COLUMNS`, including the four it never uses.
- **`grid` is by far the most influential input** (Task 33). A prediction without a grid slot has little to go on.
- **The test seasons have been used.** Any further change to the model or threshold that is judged on test scores would turn them into a second validation set.
- **Numbers for the report:** the podium rate is 13.67% after cleaning (15.1% in validation and test), the validation set is small (775 rows, 117 podiums, 39 races), and differences below about 0.02 PR-AUC are noise.
- **Limitations already measured:** thin qualifying coverage before 2003, history features that transfer less well to the 2022–2024 test seasons than the starting position does (Task 31), in-race events that no pre-race feature can contain (Task 34), and the small test set (68 races).
