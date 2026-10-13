# Formula 1 Podium Prediction

<div class="subtitle">CSEN 903 · Milestone 1 · Analytical Report</div>

<div class="meta">
<b>Team:</b> TEAM MEMBER NAMES AND IDS<br>
<b>Notebook (Kaggle):</b> KAGGLE NOTEBOOK LINK<br>
<b>Repository:</b> https://github.com/Abdel-RahmanIII/Formula-1<br>
<b>Date:</b> 18 October 2026
</div>

## 1. Summary

**Task.** Predict whether a driver finishes on the podium (top three) of a Formula 1 race, using only information available after qualifying and before the start. The data are the 14 relational tables of the Ergast Formula 1 dataset, 1950–2024.

**What was built.** One notebook that audits and cleans the raw tables, answers three data-engineering questions, builds a table of 21 pre-race features with one row per driver per race, trains and compares five models, measures what each feature group contributes, explains the selected model, and wraps it in an inference function.

**Main results**

- **The modeling table has 24,575 rows**, one per `(raceId, driverId)`, after removing the Indianapolis 500 races, 1,715 non-starters and 64 surplus shared-drive rows from the 26,759 raw rows.
- **All four learned models beat the baseline, and none beats the others.** On the unseen test seasons (2022–2024) PR-AUC is 0.701 to 0.711 for the learned models, against 0.647 for a rule that predicts the first three grid slots. The pre-race features are worth about 0.06 PR-AUC; model complexity adds nothing measurable.
- **The model is mostly a model of the starting grid.** Starting position (grid and qualifying) carries most of the signal, the recent results of the driver and team add a measurable amount, and race context adds nothing.
- **No data leakage.** Every history feature uses only earlier races. Two tests in the notebook verify this, and the inference function reproduces the features from pre-race information alone.
- **The limit is the race itself.** The clearest errors are results decided by in-race events, which no pre-race input contains.

The split, used throughout: **train** on seasons up to 2019, **validate** on 2020–2021, **test** on 2022–2024. A split by time is used because a random split would train on later seasons than it tests on, and would leak era-specific knowledge about which teams are fast.

| Split | Rows | Races | Podiums | Podium rate |
| :--- | ---: | ---: | ---: | ---: |
| Train (≤ 2019) | 22,448 | 1,007 | 3,038 | 13.53% |
| Validation (2020–2021) | 775 | 39 | 117 | 15.10% |
| Test (2022–2024) | 1,352 | 68 | 204 | 15.09% |

Every judgment call is recorded with its evidence in the decision log of the repository (DEC-001 to DEC-033); the identifiers are cited below.

## 2. Data Audit and Cleaning

### 2.1 Audit of the raw tables

- **Size.** 14 tables, 701,433 rows. `results` has 26,759 rows over 1,125 races. `lap_times` is 84% of all rows and is recorded during the race, so it is forbidden as a feature.
- **Primary keys.** All 16 keys checked (single and composite) are unique and non-null, with one known exception handled in cleaning: `results` has repeated `(raceId, driverId)` pairs.
- **Foreign keys.** All 22 foreign keys were reconciled with anti-joins. None has an orphan row.
- **Sentinels.** Missing values are written as the text `\N`. They are read as missing at load time.
- **Raw tables are never modified.** All cleaning works on copies, and the notebook asserts at the end that the raw tables equal a fresh load.

Two findings from the "before" plots shaped later decisions:

- **Qualifying coverage drifts.** There is no qualifying data before 1994, coverage is between 6% and 59% of result rows in 1996–2002, and it is complete only from 2003.
- **The podium rate depends on field size.** It is 12.69% over all raw rows, falls to 7.74% in 1989 when entry lists were longest, and is near 15% in the modern 20-car era.

![Qualifying coverage per season](before_eda_qualifying_coverage.png)
<div class="caption">Figure 1. Rows per season in <code>results</code> and <code>qualifying</code> (top) and qualifying rows as a share of result rows (bottom). Qualifying is complete only from 2003.</div>

### 2.2 Cleaning steps

| Step | Rule | Rows removed | Rows left |
| :--- | :--- | ---: | ---: |
| Raw `results` | | | 26,759 |
| Scope (DEC-003) | Drop the Indianapolis 500 races of 1950–1960: run to different rules, on an oval, with a different field | 405 | 26,354 |
| Non-starters (DEC-009) | Drop a row when the driver completed zero laps **and** is labelled as not qualified or withdrawn, or had no grid slot | 1,715 | 24,639 |
| Shared drives (DEC-008) | Where a driver has several rows in one race, keep the car they started in; break ties by best finishing position | 64 | 24,575 |

- **Semantic typing.** Dates are converted to datetime. Qualifying times and pit-stop durations such as `"1:24.312"` are converted to seconds (84.312). The count of missing values is the same before and after conversion, so no time was lost in parsing.
- **Why "zero laps" is part of the non-starter rule.** The label alone is unreliable: 1,724 rows carry a non-starter label, but 24 of them completed racing laps. No podium finisher is removed.
- **Duplicates.** In the 1950s a driver could take over a teammate's car mid-race, and each car got its own row: 176 rows in 85 driver-race pairs, almost all from 1953–1956. The deterministic rule above leaves exactly one row per `(raceId, driverId)`, which the notebook asserts.
- **Pit-lane starts (DEC-010).** The 72 remaining rows with `grid = 0` are real pit-lane starts. Left as 0, a model would read them as better than pole. They get `pit_start = 1` and a grid slot one place behind the last car.

### 2.3 Effect of cleaning

- **8.2% of raw rows are removed**, most of them non-starters from the crowded entry lists of the 1970s to 1990s. The largest "field" falls from 55 entries to 34 starters.
- **The podium rate rises from 12.69% to 13.67%.** From the mid-1990s the before and after lines coincide, so cleaning does not distort the seasons used for validation and testing.
- **Fifteen races of 1950–1960 keep four or five podium rows**, because two drivers were classified in the same podium car. They are kept on purpose.

![Rows removed by each cleaning stage](after_eda_row_count_waterfall.png)
<div class="caption">Figure 2. Rows remaining after each cleaning stage (dark) and rows removed by that stage (red). The axis starts at 22,000.</div>

![Podium rate before and after cleaning](after_eda_podium_base_rate.png)
<div class="caption">Figure 3. Podium rate per season before (grey, dashed) and after (red) cleaning. The shaded bands are the validation and test seasons.</div>

## 3. Data-Engineering Questions

The three questions are descriptive analyses. Outcome columns such as `podium` and `status` are what is being measured; they are never model features. Every grouping variable is known before the race.

### 3.1 Q1: Which circuits convert a front-row start into a podium, and did the ranking change after 2014?

**Answer. Front-row starts convert more often in the hybrid era, and the circuit ranking is only loosely preserved.**

- **Overall.** A front-row start ended on the podium 68.3% of the time in 2003–2013 and 76.2% in 2014–2024. The rate rose at 11 of the 14 ranked circuits.
- **Top circuits, 2014–2024.** Monaco (89.5%), Suzuka (88.9%), Yas Marina (86.4%). The Hungaroring is last (59.1%).
- **Top circuits, 2003–2013.** Monaco and Monza (both 77.3%), then Silverstone (72.7%).
- **Ranking.** The Spearman correlation between the two eras is 0.36 (p = 0.21) on the grid definition and 0.54 (p = 0.05) on the qualifying definition. Monaco and Suzuka stay near the top; Monza falls from 1st to 10th.
- **Grid vs. qualifying position.** Grid penalties moved 9 of 398 top-two qualifiers (2.3%) off the front row in 2003–2013 and 27 of 453 (6.0%) in 2014–2024. The two definitions still rank the circuits almost identically (correlation 0.89 and 0.88).
- **How far to trust it.** Each circuit has 10 to 24 front-row starts per era, so one race moves a rate by 4 to 10 points. The rise in the overall level is solid; individual rank changes are mostly within that noise.

![Front-row conversion by circuit](de_q1_front_row_conversion.png)
<div class="caption">Figure 4. Podium rate of front-row starters per circuit, 2003–2013 (grey) and 2014–2024 (red), for both definitions of "front row".</div>

| | |
| :--- | :--- |
| **Joins** | `results` + `races` + `circuits` + `qualifying` on `(raceId, driverId)`, checked one-to-one |
| **Grain** | One row per driver per race; rates aggregated per circuit and era |
| **Missing values** | Seasons before 2003 are left out, because the qualifying file is missing whole races before then (DEC-011). Circuits with fewer than 10 front-row starts in either era are not ranked |
| **Pre-race cutoff** | Grid slot and qualifying position are both fixed before the start. `podium` is used only as the outcome |

### 3.2 Q2: Do drivers reach the podium more often at home, after controlling for starting position?

**Answer. No. Once starting position is held fixed, there is no detectable home advantage.**

- **Before controlling for grid** the home rate is lower: 11.92% at home against 13.82% away. That gap comes from where home drivers start: 11.8% of home starts are from the first three grid slots, against 13.7% of away starts.
- **Within grid buckets** (1, 2–3, 4–6, 7–10, 11+) the difference goes both ways, from −3.7 points on pole to +4.2 points from slots 2–3, and every pair of intervals overlaps.
- **Significance.** The Cochran–Mantel–Haenszel pooled odds ratio for a home race is 0.95 (95% interval 0.80 to 1.13, p = 0.61). A logistic regression of podium on home race and grid bucket agrees: 0.95 (0.79 to 1.16, p = 0.63).
- **Robustness.** The result holds with the exact grid slot instead of buckets (0.97), with only drivers who ever had a home race (0.94), and with the decade added (0.94).
- **What it rules out.** A large home advantage: at most about 13% higher odds. It does not rule out a home effect on qualifying itself, because conditioning on grid removes that channel by design.

![Home advantage by grid bucket](de_q2_home_advantage.png)
<div class="caption">Figure 5. Podium rate at home and away within each grid bucket, with 95% intervals.</div>

| | |
| :--- | :--- |
| **Joins** | `results` + `races` + `circuits` + `drivers` on `driverId` |
| **Grain** | One row per driver per race: 24,575 starts, of which 1,930 (7.9%) are home starts |
| **Missing values** | Every nationality is mapped to its home countries (asserted, DEC-012) and no row lacks a grid slot. Drivers from countries without a circuit stay in the away group |
| **Pre-race cutoff** | Nationality, circuit country and grid slot are known before the start. `podium` is the outcome |

### 3.3 Q3: Which constructors have the highest mechanical-retirement rate in 2014–2021 and in 2022–2024?

**Answer. 2014–2021: Lotus F1, Toro Rosso and Renault. 2022–2024: Alfa Romeo, Alpine and AlphaTauri.**

| Era | Highest rates (retirements of starts) | Lowest |
| :--- | :--- | :--- |
| 2014–2021 | Lotus F1 18.7% (14 of 75), Toro Rosso 16.1% (39 of 242), Renault 14.1% (28 of 199) | Aston Martin 2.3% (1 of 44), Mercedes 4.1% (13 of 320) |
| 2022–2024 | Alfa Romeo 12.5% (11 of 88), Alpine 10.4% (14 of 135), AlphaTauri 8.0% (7 of 88) | Sauber 2.1% (1 of 48), Red Bull and McLaren 3.7% (5 of 136) |

- **Definition (DEC-013).** All 139 status values are mapped to one of four categories: finished, mechanical, accident or driver error, and regulatory or other. A mechanical retirement is a start that ended with a failed car component. The denominator is race starts, not entries.
- **Reliability improved across the field:** from 9.43% of starts in 2014–2021 to 5.92% in 2022–2024.
- **Same team across eras (DEC-014).** With renamed teams merged, the Lotus F1 / Renault / Alpine team is the least reliable in both eras. McLaren improved most, from 13.6% to 3.7%.
- **Sensitivity.** Counting the generic `Retired` label as mechanical leaves the 2014–2021 ranking almost unchanged; in 2022–2024 Alfa Romeo stays first but the order below it moves.
- **How far to trust it.** The intervals are wide, especially in 2022–2024, where the top three are separated by 4 to 7 retirements. The leaders are clear; the middle of each ranking is not.

![Mechanical retirement rate by constructor](de_q3_mechanical_retirements.png)
<div class="caption">Figure 6. Mechanical retirements per race start, per constructor and era, with 95% intervals. Constructors with fewer than 40 starts in an era are not ranked.</div>

| | |
| :--- | :--- |
| **Joins** | `results` + `races` + `status` on `statusId` + `constructors` on `constructorId` |
| **Grain** | One row per driver per race start, aggregated per constructor and era; 4,597 starts from 2014 on |
| **Missing values** | Every status is mapped (asserted) and every row has a status and a constructor |
| **Pre-race cutoff** | `status` is recorded after the race and is used only as the outcome. As a model feature it would be allowed only as an aggregate of earlier races |

## 4. Features

### 4.1 Feature registry with temporal validity

The modeling table has 21 features in six groups. The last column states why each value is known before the race starts.

| Group | Feature | Source tables | Definition | Why it is known before the race |
| :--- | :--- | :--- | :--- | :--- |
| Grid | `grid` | results | Starting slot; pit-lane starts recoded behind the last car | Set after qualifying and penalties |
| | `pit_start` | results | 1 if the car started from the pit lane | Set before the start |
| | `front_row` | results | 1 if grid is 1 or 2 | Derived from grid |
| | `teammate_grid_diff` | results | Grid slot minus the mean slot of the team's other cars | Derived from grid |
| Qualifying | `quali_position` | qualifying | Qualifying classification, before grid penalties | Qualifying ends before the race |
| | `gap_to_pole` | qualifying | Best of Q1–Q3, % slower than the fastest qualifier | Qualifying ends before the race |
| | `q3_reached` | qualifying | 1 if a Q3 time was set | Qualifying ends before the race |
| | `missing_quali_flag` | qualifying | 1 if the row has no qualifying record | Known from the data itself |
| Driver form | `driver_rolling_podium_rate_5` | results, races | Podium rate over the driver's last 5 races | Shifted by one race: earlier races only |
| | `driver_rolling_avg_finish_5` | results, races | Mean finishing order over the last 5 races | Shifted by one race: earlier races only |
| | `driver_career_podium_rate` | results, races | Podium rate over all earlier races | Shifted by one race: earlier races only |
| Constructor form | `constructor_rolling_podium_rate_5` | results, races | Podiums per car entered over the team's last 5 races | Shifted by one race: earlier races only |
| | `constructor_rolling_points_5` | results, races | Team's share of all points awarded in its last 5 races | Shifted by one race: earlier races only |
| Standings | `driver_pre_race_points` | driver_standings, races | Driver's points as a share of the leader's, after the previous round | Standings of the previous round, same season |
| | `driver_pre_race_rank` | driver_standings, races | Championship position after the previous round | Standings of the previous round, same season |
| | `constructor_pre_race_points` | constructor_standings, races | Team's points as a share of the leader's, after the previous round | Standings of the previous round, same season |
| | `constructor_pre_race_rank` | constructor_standings, races | Constructors' championship position after the previous round | Standings of the previous round, same season |
| Context | `field_size` | results | Number of starters in the race | The grid is final before the start |
| | `round` | races | Round number within the season | Calendar |
| | `is_home_race` | drivers, circuits | 1 if the circuit is in the driver's home country | Static attributes |
| | `circuit_historical_podium_rate` | results, races | Driver's podium rate in earlier races at this circuit | Shifted by one race: earlier races only |

Three design choices need a word:

- **Standings are taken from the previous round.** The dataset stores standings as they stood *after* each race. Using the row of the same race would leak the result, so the row of round *r − 1* is used for round *r*.
- **Points are shares, not totals (DEC-015).** A win was worth 8 to 10 points until 2009 and 25 from 2010. Dividing by the points awarded, or by the leader's points, keeps the feature on one scale across eras.
- **Sprint results are left out (DEC-016).** The first sprint was held in 2021, so the training seasons contain none and a model cannot learn from the column.

### 4.2 Proof that the features do not leak

A written rule is not a proof, so the notebook tests the feature table directly.

- **A blacklist enforced in code.** Race-outcome columns (finishing position, points, laps, race time, fastest lap, status) are listed once, and `assert_leakage_safe()` rejects any feature list that contains one of them.
- **Test 1, independent recomputation.** For 300 random rows, six history features are recomputed the slow way, using only rows with an earlier date. They match the feature table.
- **Test 2, corrupting the future.** For 20 random races, every outcome from that race onward is scrambled and the feature table is rebuilt. The 21 features of that race do not change. A control feature built without the one-race shift is flagged in 20 of 20 races, which shows the test can detect leakage.
- **Test 3, rebuilding at inference time.** The inference function builds features from the races before the requested one, with the requested race's results blanked. For 36 validation and test rows the rebuilt features and model scores are identical to the feature table (Section 9).

### 4.3 Evidence behind the feature set

- **Grid position is the strongest signal available for every row.** The podium rate falls from 63.3% on pole to 5.7% from tenth and 0.8% from twentieth. Used alone, `grid` has a ROC-AUC of 0.883.
- **Qualifying adds a little where it exists.** `quali_position` (0.905) and `gap_to_pole` (0.887) rank podiums slightly better than `grid`, but they are present in only 37% of the training rows.
- **Form and standings carry real signal:** each of those features scores between 0.79 and 0.84 alone.
- **Four features have almost none alone** (`pit_start`, `is_home_race`, `round`, `missing_quali_flag`, ROC-AUC 0.50 to 0.51). `is_home_race` agrees with Q2. They were kept so the ablation could measure them properly; Section 7 confirms they add nothing.
- **Several features overlap.** `quali_position` and `grid` correlate at 0.98. This matters for how the ablation and the explanations must be read.
- **A rolling window of 5 races is enough (DEC-018).** With the career rate alongside, the driver-form features reach 0.843 with 5 races and 0.846 with 10.

![Podium rate by grid position](feat_podium_rate_by_grid.png)
<div class="caption">Figure 7. Podium rate for each grid position in the training seasons, with 95% intervals. The dashed line is the training base rate.</div>

![Single-feature ROC-AUC](feat_univariate_auc.png)
<div class="caption">Figure 8. ROC-AUC of each feature used alone, coloured by feature group. 0.5 is no signal.</div>

## 5. Split and Preprocessing

**Pipeline.** For models that need complete, scaled inputs: a missing qualifying position is filled with the grid slot, the 16 continuous features are imputed with the training median and standardised, and a missing flag is filled with 0. Everything is fitted on the training seasons only. No encoder is needed (DEC-020): every feature is numeric or a 0/1 flag, and driver and team identifiers are not one-hot encoded, because many validation and test rows belong to drivers or teams that never appear in training.

**Training window (DEC-019).** Because qualifying is missing in 63% of training rows, the window was tested instead of assumed.

| Training window | Train rows | Logistic regression, validation PR-AUC | Gradient boosting, validation PR-AUC |
| :--- | ---: | ---: | ---: |
| All seasons | 22,448 | 0.728 | 0.704 |
| From 1994 | 10,091 | 0.720 | 0.704 |
| From 2003 | 6,782 | 0.725 | 0.693 |
| From 2006 | 5,743 | 0.729 | 0.665 |

The window makes no real difference to the logistic regression and less data hurts gradient boosting, so all seasons are used.

**Preprocessing-order experiments (DEC-021).** Both are scored on validation with a logistic regression, with a 95% interval from resampling whole races 500 times.

| Experiment | Variants compared | Difference in validation PR-AUC (95% interval) |
| :--- | :--- | :--- |
| 1. Scope of fitting | Preprocessor fitted on train only vs. on all rows | 0.0000 (−0.0005 to +0.0003) |
| 2. Order of steps | Impute then scale vs. scale then impute | −0.0001 (−0.0006 to +0.0001) |

Neither changes the score here, and the notebook shows why. In experiment 1 the validation and test seasons are only 8.7% of the rows, so the fitted medians and standard deviations barely move. In experiment 2 the scaler does learn a different standard deviation (1.57 against 2.57 for `gap_to_pole`), but a logistic regression adjusts its coefficient to compensate. Fitting on train only and imputing first are kept because they are correct by construction, not because they score higher.

**Distribution shift.** Validation and test are not distributed like training: `field_size` sits almost one training standard deviation below the training mean (modern grids have 20 cars) and `round` is higher (longer seasons). This is a reason to validate on recent seasons.

![Distribution shift between splits](prep_distribution_shift.png)
<div class="caption">Figure 9. Mean of each scaled feature in the validation and test seasons. Zero is the training mean.</div>

## 6. Models

### 6.1 Protocol

- **Main metric: PR-AUC.** About 15% of rows are podiums. PR-AUC measures how well a model ranks those few positives without needing a threshold. ROC-AUC is reported beside it but moves little, because it also rewards ranking the many easy back-of-grid rows.
- **Secondary metric: F1** at a decision threshold, with precision and recall. The threshold of each model is the one with the highest F1 on validation (DEC-028).
- **Every model is fitted on the training seasons only, and every choice is made on validation:** hyperparameters, the network's stopping epoch, the thresholds and the selected model. The test seasons were scored once for the comparison below, after all of those were fixed (DEC-030).
- **Uncertainty.** Differences between models are given a 95% interval by resampling whole races 500 times.

### 6.2 The five models

| Model | Input | Tuning |
| :--- | :--- | :--- |
| Grid ≤ 3 rule (baseline) | `grid` only | None: predicts a podium for the first three grid slots |
| Logistic regression (baseline) | 21 preprocessed features | None. `C` from 0.01 to 100 gives 0.727 to 0.728 |
| Random forest | 21 preprocessed features | 20 random configurations; the best has trees of depth 4 |
| LightGBM (gradient boosting) | 21 raw features, missing values included | 40 random configurations; the best has 100 trees of 8 leaves |
| Shallow neural network (Keras) | 21 preprocessed features | 8 architectures; the best has two hidden layers (64 and 32 units), dropout 0.2, early stopping on validation PR-AUC |

All learned models use balanced class weights. Measured directly (DEC-027), the weights do not change the ranking, but they double the model output: the result is a score, not a probability. Section 9 returns to this.

### 6.3 Results on all three splits

| Model | Split | ROC-AUC | PR-AUC | F1 | Precision | Recall |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| Grid ≤ 3 rule | Train | 0.883 | 0.500 | 0.544 | 0.547 | 0.541 |
| | Validation | 0.910 | 0.648 | 0.695 | 0.698 | 0.692 |
| | Test | 0.913 | 0.647 | 0.649 | 0.650 | 0.647 |
| Logistic regression | Train | 0.901 | 0.562 | 0.582 | 0.470 | 0.764 |
| | Validation | 0.929 | 0.728 | 0.709 | 0.657 | 0.769 |
| | Test | 0.936 | 0.711 | 0.673 | 0.554 | 0.858 |
| Random forest | Train | 0.906 | 0.588 | 0.591 | 0.522 | 0.680 |
| | Validation | 0.931 | 0.739 | 0.712 | 0.669 | 0.761 |
| | Test | 0.938 | 0.710 | 0.678 | 0.588 | 0.799 |
| LightGBM | Train | 0.909 | 0.592 | 0.592 | 0.535 | 0.662 |
| | Validation | 0.930 | 0.743 | 0.714 | 0.703 | 0.727 |
| | Test | 0.940 | 0.709 | 0.689 | 0.623 | 0.770 |
| Neural network | Train | 0.914 | 0.602 | 0.584 | 0.580 | 0.588 |
| | Validation | 0.929 | 0.738 | 0.721 | 0.724 | 0.718 |
| | Test | 0.936 | 0.701 | 0.662 | 0.631 | 0.696 |

Test PR-AUC compared with the logistic regression: random forest −0.002 (95% interval −0.027 to +0.023), LightGBM −0.002 (−0.029 to +0.022), neural network −0.011 (−0.035 to +0.015), grid rule −0.064 (−0.117 to −0.010).

### 6.4 What the results say

- **The features are worth about 0.06 PR-AUC over the grid rule.** This is the only difference in the table whose interval excludes zero.
- **Model complexity adds nothing measurable.** The untuned logistic regression is level with the forest and LightGBM on test and slightly ahead of the network. This answers the brief's question of whether model complexity is justified: on this data it is not.
- **Tuning on a small validation set flattered the tuned models.** From validation to test the logistic regression loses 0.017, the forest 0.030, LightGBM 0.033 and the network 0.037.
- **Training scores are the lowest in every row.** The training seasons run from 1950, have a lower podium rate and mostly lack qualifying data, so they are harder to predict than 2020–2024. No model has a training score far above its validation score, so none is overfitted.
- **The tuned thresholds are too low for the test seasons.** They predict 3.3 to 4.6 podiums per race where there are 3. Picking the three highest-scoring drivers of each race instead gets about two of the three places right, the same as the grid rule.
- **LightGBM is carried forward (DEC-029).** The rule was fixed before the test seasons were scored: the highest validation PR-AUC. On test it equals the logistic regression, which would be an equally defensible and simpler choice. The selection was not revisited after seeing the test scores.

![Precision-recall curves](model_pr_curves.png)
<div class="caption">Figure 10. Precision against recall on the validation and test seasons. The dot on each line is the model at its tuned threshold; the cross is the grid rule.</div>

## 7. Ablation

LightGBM is retrained with part of the features removed. Only the columns change: the same hyperparameters, the same training rows, no retuning (DEC-031). Each difference comes with a 95% interval from resampling races, and is also averaged over 10 random seeds, because the seed alone moves PR-AUC by about 0.006.

**Leave one group out.** No single group is significant: every interval includes zero on both splits.

| Removed group | Validation change in PR-AUC (95% interval) | Test change in PR-AUC (95% interval) |
| :--- | :--- | :--- |
| Grid | −0.015 (−0.043 to +0.007) | −0.019 (−0.043 to +0.003) |
| Qualifying | −0.019 (−0.055 to +0.010) | +0.011 (−0.005 to +0.025) |
| Standings | −0.015 (−0.041 to +0.003) | +0.006 (−0.008 to +0.020) |
| Driver form | −0.005 (−0.016 to +0.007) | −0.007 (−0.023 to +0.010) |
| Constructor form | −0.003 (−0.011 to +0.004) | −0.005 (−0.013 to +0.003) |
| Context | −0.000 (−0.009 to +0.006) | +0.001 (−0.005 to +0.006) |

This does not mean the features are useless. Leave-one-out measures what a group adds on top of all the others, and the groups overlap: grid and qualifying both say where the car starts; driver form, constructor form and standings all say how the driver and team have been doing. When one is removed, the model reads the same information from its neighbour. So the overlapping groups were also removed together, as blocks.

| Removed block | Features | Validation change (95% interval) | Test change (95% interval) |
| :--- | ---: | :--- | :--- |
| Starting position (grid + qualifying) | 8 | −0.089 (−0.145 to −0.034) | −0.123 (−0.181 to −0.072) |
| Past results (driver form + constructor form + standings) | 9 | −0.061 (−0.100 to −0.021) | −0.042 (−0.076 to −0.007) |
| Context | 4 | −0.000 (−0.009 to +0.006) | +0.001 (−0.005 to +0.006) |

- **Starting position is the larger block.** Alone it scores 0.669 on validation and 0.665 on test, about 0.02 above the grid rule.
- **Past results add 0.04 to 0.06 on top.** This is the gain Section 6 found between the grid rule and the learned models.
- **Context adds nothing** and could be dropped. It was kept because the model was fixed before the test seasons were scored.
- **History transfers less well than the starting position.** Alone, the starting position scores the same on both splits, while past results fall from 0.656 on validation to 0.591 on test.

![Leave one feature group out](ablation_leave_one_group_out.png)
<div class="caption">Figure 11. Change in PR-AUC when one feature group is removed, with 95% intervals. Every interval crosses zero.</div>

![Blocks removed and groups alone](ablation_blocks_and_alone.png)
<div class="caption">Figure 12. Left: change in PR-AUC when a block of overlapping groups is removed. Right: PR-AUC of a model trained on one group or block alone.</div>

## 8. Explainability

All explanations are of the fitted LightGBM on the validation seasons (DEC-032). Nothing is retrained.

### 8.1 Global: which features the model relies on

**Permutation importance.** A feature is shuffled across the validation rows and the drop in PR-AUC is recorded (50 shuffles).

- **`grid` alone costs 0.238** (95% range 0.155 to 0.310), about a third of the model's 0.743. No other single feature is clearly above zero.
- **`quali_position` costs 0.000**, although it is nearly the same number as `grid`: the model reads the starting position from `grid` and barely uses its copy.
- **Single-feature importances do not add up.** They sum to 0.318, while shuffling everything at once costs 0.587. A feature that has a substitute is understated, so importance is reported per block as well.

**SHAP values.** For a tree model SHAP is exact: the base value plus the 21 contributions equals the model output for every row, which the notebook asserts. The unit is log-odds of the model score.

- **`grid` carries 41% of all SHAP magnitude**, then the team's recent points (13%), the driver's recent podium rate (8%) and career podium rate (8%).
- **The effect of `grid` is a staircase:** about +1.6 for slots 1 to 3, falling by 0.3 per slot to zero between slots 9 and 10, and −1.03 for every slot from 15 back.
- **Form features act as a switch:** a driver with at least one podium in the last five races gets about +0.2, one with none about −0.13, with little difference between one podium and five.
- **Four features appear in no tree** (`pit_start`, `missing_quali_flag`, `is_home_race`, `circuit_historical_podium_rate`).

| Block | Share of SHAP magnitude | Permutation drop (fitted model) | Retraining drop (Section 7) |
| :--- | ---: | ---: | ---: |
| Starting position | 55% | 0.394 | 0.089 |
| Past results | 44% | 0.160 | 0.061 |
| Context | 0.6% | 0.000 | 0.000 |

The three measures agree on the order and differ in size because they answer different questions. Permutation scrambles a block for the fitted model, which still trusts the scrambled values. Retraining lets a new model lean on what is left.

![Permutation importance](xai_permutation_importance.png)
<div class="caption">Figure 13. Drop in validation PR-AUC when one feature is shuffled (left) and when a whole group or block is shuffled together (right).</div>

![SHAP summary plot](xai_shap_beeswarm.png)
<div class="caption">Figure 14. SHAP summary (beeswarm) plot. One dot per validation row and feature; position is the contribution to the log-odds, colour is the feature value.</div>

### 8.2 Local: two surprising results

Two validation rows were chosen by rule, not by hand: the podium finisher with the lowest score, and the pole-sitter off the podium with the highest score. Both come from the 2020 Italian Grand Prix.

| Case | Score | Result | Largest SHAP contributions (log-odds) |
| :--- | ---: | :--- | :--- |
| Pierre Gasly (AlphaTauri), grid 10 | 0.111 | Won | All negative: team's recent points −0.17, grid −0.17, no recent podium −0.12, career podium rate −0.12 |
| Lewis Hamilton (Mercedes), pole | 0.914 | Seventh | All positive: grid +1.65, team's recent points +0.33, five podiums in five races +0.27 |

In both rows the model read its inputs sensibly. Nothing in Gasly's pre-race data suggested a podium, and everything in Hamilton's did. Both results were decided during the race, and that information does not exist before the start. Errors of this kind cannot be removed by tuning; they set a limit on any pre-race model.

![SHAP waterfall, unexpected podium](xai_shap_waterfall_unexpected_podium.png)
<div class="caption">Figure 15. SHAP waterfall for Pierre Gasly, 2020 Italian Grand Prix. Read from the bottom: the plot starts at the base value and each bar adds one feature's contribution.</div>

![SHAP waterfall, pole-sitter off the podium](xai_shap_waterfall_pole_sitter_off_the_podium.png)
<div class="caption">Figure 16. SHAP waterfall for Lewis Hamilton, 2020 Italian Grand Prix.</div>

**LIME on the same two rows.** LIME fits a small linear model to the model's scores on 5,000 artificial rows around the row of interest.

| | Gasly (score 0.111) | Hamilton (score 0.914) |
| :--- | ---: | ---: |
| Fit of LIME's linear model (R²) | 0.05 | 0.83 |
| LIME's top feature | `pit_start = 0` | `grid <= 5` |
| SHAP value of that feature | 0 (never used by the model) | +1.65 |
| Rank correlation with SHAP | 0.47 | 0.89 |
| Different top features across 5 random seeds | 3 | 1 |

For Hamilton, LIME agrees with SHAP and is stable. For Gasly it fails: its linear model explains 5% of the variation, and its top feature is one the model never uses. SHAP is therefore the primary method, and LIME is quoted only together with its R².

### 8.3 What the explanations do not say

- **Importance is not causation.** `grid` is important because it summarises how fast the car and driver are that weekend. Putting a slow car on pole would not make it a podium contender. The model has learned an association that holds when drivers reach their grid slot in the usual way.
- **Credit between overlapping features is arbitrary.** `grid` and `quali_position` are nearly the same number; the model happened to use `grid`. Importance should be quoted per block.
- **A SHAP value can reflect how the data was recorded.** `q3_reached` gets about −0.1 whether or not Q3 was reached, because only 25% of training rows have a value for it.
- **The explanations describe this model on 2020–2021**, in units of a class-weighted score, not of a calibrated probability.

## 9. Inference Function

`predict_podium(raceId, driverId, grid, quali_info=None)` returns a prediction (podium or not), a calibrated probability, the raw model score and the 21 features it built (DEC-033).

- **Features are rebuilt, not looked up.** The function runs the same feature code as training on the races before the requested one, plus that race's entry list with its results blanked. For 36 validation and test rows, including pit-lane starts, the rebuilt features and scores are identical to the modeling table.
- **Missing values go to the model as missing.** LightGBM takes the raw features, so no value is invented for missing qualifying data. Most training seasons have no qualifying data, so the model has seen this in about 14,000 rows.
- **The score is calibrated before it is called a probability.** Because of the class weights the raw score averages 0.32 where 15% of rows are podiums. A one-input logistic regression fitted on validation (Platt scaling) corrects this without changing the order of the drivers. On the test seasons the mean probability is 0.161 against a podium rate of 0.151, and the Brier score falls from 0.116 to 0.068.

**Demonstration: the pole-sitter of the last race in the data** (Lando Norris, 2024 Abu Dhabi Grand Prix; he won).

| Input | Score | Probability | Prediction |
| :--- | ---: | ---: | :--- |
| Complete record | 0.902 | 0.764 | Podium |
| Qualifying position only, no lap times | 0.872 | 0.683 | Podium |
| No qualifying information | 0.864 | 0.663 | Podium |

Across the whole 2024 season, removing qualifying from every row moves PR-AUC from 0.692 to 0.690, and 12 of 476 predictions change.

![Reliability on the test seasons](inference_calibration.png)
<div class="caption">Figure 17. Share of podiums against the average predicted value, in eight equal groups of test rows. Points on the diagonal are perfectly calibrated.</div>

## 10. Limitations and Future Work

**Data**

- **Historical qualifying drift.** The four qualifying features are missing in 63% of the training rows and in almost none of the validation and test rows. The model learns the value of qualifying from about a third of its training data.
- **The training seasons are unlike the test seasons.** Training runs from 1950: larger and more variable fields, a lower podium rate, different points systems.
- **Era boundaries are not modelled.** Regulation changes (2014, 2022) reshuffle which teams are fast, and the model sees them only through form and standings, which lag by a few races. Features built from past results transfer less well to 2022–2024 than the starting position does.
- **Constructor identity breaks at rebrands.** A renamed team starts its rolling history from nothing. The lineage mapping built for Q3 was not used for the features.

**Evaluation**

- **Small validation and test sets.** 39 and 68 races. Intervals on PR-AUC differences are about ±0.02 to ±0.03, so the learned models cannot be separated.
- **The thresholds do not transfer well** from validation to test.
- **The test seasons have been used.** One model comparison was made on them and nothing was chosen from it. They were scored again to describe the features (Section 7) and to check the calibration (Section 9). They are no longer untouched data for any future change.

**Model**

- **In-race events set a ceiling.** Crashes, safety cars, penalties, weather and strategy are not in the inputs.
- **Four of the 21 features are never used**, and the context group contributes nothing.
- **The output is unreliable for unusual inputs.** For a front-running car starting last, the function's output rises, which the training data does not support.
- **The inference function works only for races in the dataset**, whose history ends with the 2024 season.

**Future work**

- Use the lineage of renamed teams in the features.
- Drop the unused features and compare a logistic regression with LightGBM on a new, untouched season.
- Rank drivers within a race instead of scoring rows independently, since every race has exactly three podium places.
- Add pre-race information the dataset does not hold: practice pace, weather forecast, tyre allocation.
- Tune with several consecutive validation windows instead of one 39-race window.
