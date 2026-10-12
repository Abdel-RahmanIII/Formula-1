# Notebook Guide: what each part of `formula-1.ipynb` does

This guide walks through [formula-1.ipynb](../formula-1.ipynb) in order: what each code cell does, why it is there, and how to read each figure. All numbers come from a full run of the notebook on the local `archive/` data (pandas 2.3.3).

**The project in one paragraph.** We predict whether a driver finishes on the podium (top three) in a Formula 1 race. The prediction is made after qualifying and before the race starts, so nothing that happens during or after the race may be used as an input. The notebook so far loads the 14 raw tables, checks them, cleans them and produces one table, `clean_df`, that the rest of the team builds on.

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

A copy of decisions DEC-001 to DEC-007 and a short list of which tables are safe. The full log, including the three cleaning decisions DEC-008 to DEC-010, is in [decision_log.md](decision_log.md).

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

## Is Member 1's work done?

**The technical steps are done; the role is not.** Steps 1 and 2 of the plan (Tasks 1–8: audit, cleaning, before/after plots) are complete, and `clean_df` passes the data contract. What M1 still owes, according to [milestone_1_plan.md](milestone_1_plan.md):

| M1 item | Status |
| :--- | :--- |
| Load, audit, clean, before/after EDA | Done |
| Commit and push the notebook, figures and decision log | **Not done.** The work is only in the local working copy, so teammates cannot pull `clean_df` yet. |
| Team approval of DEC-009 and DEC-010 | **Open.** Both are still marked "Proposed". Changing either changes the row counts. |
| Repo setup: `requirements.txt`, README, `.gitignore` | Not done |
| Kaggle setup and a full Run All there | Not done; the notebook has never run on Kaggle |
| Fix stale numbers and broken `file:///d:/` links in the docs | Not done |
| Final report assembly (Step 10) | Not started |

## Next steps

**Today (M1)**

1. Review, commit and push `formula-1.ipynb`, the 11 figures and the decision log.
2. Get a yes or no from the team on DEC-009 and DEC-010.
3. Add a pinned `requirements.txt` (pandas, numpy, matplotlib, seaborn) and remove the `d:/GUC/...` path from the config cell.
4. Run the notebook once on Kaggle. The dataset there may be a newer version, which would shift the row counts.

**Rest of the team, now unblocked by `clean_df`** (deadline 18 October, 11:59 PM)

| Step | Owner | What |
| :--- | :--- | :--- |
| 3 | M2 | The three data-engineering questions: front-row conversion by circuit, home advantage, mechanical retirements by constructor. |
| 4 | M3 | Leakage-safe features from `FEATURE_GROUPS`: grid, qualifying, driver and constructor form, lagged standings, context. |
| 5 | M3 | Time-based split, preprocessing pipeline, the two preprocessing-order experiments. |
| 6 | M4 | Baselines (`grid ≤ 3` rule, logistic regression), random forest, gradient boosting, shallow neural network, tuning. |
| 7 | M3 | Ablation by feature group. |
| 8 | M2 | Explainability (permutation importance, SHAP, LIME). |
| 9 | M4 | `predict_podium()` inference function. |
| 10 | All | Final Kaggle Run All, report PDF, rehearsal. |

**Things to carry into those steps**

- The podium rate is 13.67%, not the 15% quoted in the older docs. Use PR-AUC as the main metric.
- Qualifying features need a missing flag and a `grid` fallback for seasons before 2003.
- The validation set is small (775 rows, 117 podiums), so tuning results will be noisy.
- One qualifying time is an outlier: 1995 Japanese GP, `raceId` 255, `driverId` 87, `q1` = 1,002.64 s.
