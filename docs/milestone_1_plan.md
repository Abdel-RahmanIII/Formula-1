# CSEN 903 · Milestone 1
## F1 Podium Prediction: Team Plan

A step-by-step plan for a team of four, covering individual tasks, shared components, and the technical plan.

**Deadline:** 18 October 2026, 11:59 PM.  
**Deliverables:** Kaggle notebook link, GitHub repo link, and the report as a PDF.  
**Data Split (from the intro doc):** Train $\le 2019$, Validation $2020\text{–}2021$, Test $\ge 2022$.

---

## 1. How to Organize the Team

Split the work by pipeline stage, so each person owns one stage end to end. Everyone still has to be able to defend every stage at the evaluation, which is covered in [Section 4](#4-timeline).

| Member | Role | Owns |
| :--- | :--- | :--- |
| **M1** | Data lead | Loading, audit, cleaning, before/after EDA, repo/Kaggle setup, final report assembly |
| **M2** | Analytics lead | The 3 data-engineering questions, status and nationality mappings, XAI section |
| **M3** | Features lead | Leakage-safe features, feature EDA, split, preprocessing pipeline, preprocessing-order experiments, ablation |
| **M4** | Modeling lead | Baselines, statistical models, shallow NN, tuning, thresholds, comparison table, inference function |

> **Primary Dependency:** Everyone needs clean data. **M1** should ship a quick "v0" cleaned dataset by Day 2, then refine it while the others build on top.

---

## 2. Shared Components (Agree on These on Day 1)

These are the pieces that break the project if members handle them inconsistently.

* **Config Cell:** One cell at the top of the notebook holds the random seed, split years, file paths, and a flag for whether to exclude the Indianapolis 500. Everyone imports from it; nobody hard-codes these values.
* **Leakage Blacklist:** Keep a written list of columns that are **never** features. It covers anything from the current race:
  * `position`, `positionText`, `positionOrder`, `points`, `laps`, `time`, `milliseconds`, `fastestLap*`, `statusId`
  * `pit_stops`, `lap_times`, and `constructor_results` for the current race
  * Driver and constructor standings after the current race  
  *(M3 enforces the list; M4 double-checks it).*
* **Data Contract:** Agree up front on the shape of the final modeling table:
  * One row per `(raceId, driverId)`.
  * Identifier columns: `raceId`, `driverId`, `constructorId`, `date`, `year`.
  * Target column: `podium`.
  * Feature columns, plus a `FEATURE_GROUPS` dict mapping group names to columns (ablation and XAI rely on this dict).
* **Decision Log:** A shared doc where every judgment call gets one line: what you chose, why, and the evidence (e.g., duplicate rule, Indy 500 exclusion, pit-lane starts, DNQ rows, sprint usage, and training window). This log becomes the backbone of the report and evaluation prep.
* **Repo Workflow:** Each member develops in their own section notebook or `.py` module, merged into one run-all notebook. Merge into `main` only through reviewed pull requests (at least one peer review per PR).
* **Plot Style:** Use one plotting helper with consistent titles, axes, and saving to `figures/`, so figures drop directly into the report.

---

## 3. Technical Plan, Step by Step

### Step 1: Setup and Audit (M1, Days 1–2)
* Load all 14 CSVs with `na_values=[r'\N']`. Keep raw dataframes untouched; clean copies only.
* Run a **"before" EDA**:
  * Row counts per table.
  * Missingness heatmap per table.
  * Rows and entrants per season.
  * Qualifying coverage per season (highlights the "coverage drift" warned in the brief).
  * Podium base rate per season.
* Check primary keys are unique and non-null:
  * `results.resultId`, `races.raceId`, `drivers.driverId`, etc.
  * Composite keys such as qualifying `(raceId, driverId)`.
* Check foreign-key reconciliation using anti-joins (e.g., are all `results.raceId` values present in `races`? All `results.statusId` in `status`?). Report orphan counts.

---

### Step 2: Cleaning (M1, Days 2–4)
* **Semantic Typing:**
  * Convert `races.date` (and time columns) to datetime.
  * Convert qualifying Q1/Q2/Q3 string times (e.g., `"1:23.456"`) to seconds.
  * Convert milliseconds and pit/lap durations to numeric.
* **Duplicates in `(raceId, driverId)`:**
  * Count them and report seasons of origin (mostly 1950s expected).
  * Apply a defensible rule: keep the car the driver started in (`grid > 0`), breaking ties using best `positionOrder`.
  * Document the rule and affected row counts in the decision log.
* **Scope Decisions (logged):**
  * Exclude the Indianapolis 500 ($1950\text{–}1960$).
  * Drop DNQ/DNPQ rows (known non-starters at prediction time).
  * Handle `grid = 0` by verifying it represents a pit-lane start, recoding to back-of-grid + adding a `pit_start` boolean flag.
* **"After" EDA:** Repeat Step 1 plots on cleaned data to document the effect of cleaning (e.g., changes in podium base rate, drop in missingness).

---

### Step 3: Data-Engineering Questions (M2, Days 2–7)
Each question requires four deliverables: the answer, a visualization, joins used, and notes on grain, missingness, and the pre-race cutoff.

* **Q1: Front-row conversion by circuit, before vs. after 2014**
  * Joins: `results` + `races` + `circuits` + `qualifying`.
  * Compute rate twice: front row defined as $\text{grid} \in \{1, 2\}$ vs. $\text{qualifying.position} \in \{1, 2\}$. Highlight grid penalty discrepancies.
  * Apply minimum-sample threshold (e.g., $\ge 10$ front-row starts per circuit per era).
  * Compare rankings pre-2014 vs. $2014+$ using Spearman rank correlation.
  * Visualization: Dumbbell or side-by-side bar chart.
  * *Note:* Qualifying data only reliably exists from the mid-1990s onward.

* **Q2: Home advantage, controlling for grid**
  * Joins: `results` + `drivers` + `races` + `circuits`.
  * Construct a `nationality` $\to$ `country` mapping table (e.g., `"British"` $\to$ `"UK"`, `"American"` $\to$ `"USA"`), documenting edge cases.
  * Bucket grid positions ($1$, $2\text{–}3$, $4\text{–}6$, $7\text{–}10$, $11+$) and contrast home vs. away podium rates within each bucket.
  * Test statistical significance with logistic regression ($\text{podium} \sim \text{home} + C(\text{grid\_bucket})$) or a Cochran–Mantel–Haenszel test.
  * Visualization: Grouped bar chart across grid buckets.

* **Q3: Mechanical retirement rate by constructor, 2014–2021 vs. 2022–2024**
  * Joins: `results` + `status` + `constructors` + `races`.
  * Build a comprehensive `status` $\to$ `category` mapping: *finished*, *mechanical*, *accident/driver*, *regulatory/other*.
  * Denominator: Race starts (not entries).
  * Apply minimum-starts threshold per constructor.
  * Visualization: Slope chart or side-by-side bar chart.

---

### Step 4: Feature Engineering (M3, Days 3–8)
All features must use strictly pre-race information. Form features must sort chronologically by date and apply `.shift(1)` prior to rolling or expanding window computations.

| Group | Features |
| :--- | :--- |
| **Grid** | `grid`, `pit_start`, `front_row`, grid relative to teammate |
| **Qualifying** | Quali position, gap to pole (seconds or %), `q3_reached`, missing-indicator flag |
| **Driver form** | Rolling podium rate and average finish over last $N$ races, career expanding podium rate |
| **Constructor form** | Rolling podium rate and points over last $N$ races (both cars combined) |
| **Standings** | Driver and constructor points/rank entering this race (previous round, same season; `NaN` or $0$ for round 1) |
| **Context** | Field size, round number, home-race flag, circuit-specific historical podium rate |
| **Sprint (optional)**| Same-weekend sprint result (strictly pre-race; deliberate decision logged) |

* **Feature Validation:**
  * Plot podium rate vs. grid position.
  * Feature correlation matrix.
  * Distribution of features split by class label.
  * Leakage unit test: assert that rolling/expanding calculations for row $t$ strictly reference races where $\text{date} < \text{date}_t$.

---

### Step 5: Split and Preprocessing (M3, Days 6–9)
* **Temporal Split:** Train $\le 2019$, Validation $2020\text{–}2021$, Test $\ge 2022$. (Random splits leak era-specific technical regulations).
* **Window Experiment:** Evaluate training on all years vs. $\ge 1994$ vs. $\ge 2006$ to mitigate early qualifying-coverage drift.
* **Pipeline:** Construct an `sklearn.pipeline.Pipeline` with an imputer, scaler, and encoder fitted **strictly on train**. Plot feature distributions before and after each transformation.
* **Order Experiments (run in distinct cells with metric deltas):**
  1. Scaler/imputer fitted on all data vs. fitted on train only (quantifies data leakage).
  2. Impute $\to$ scale vs. scale $\to$ impute, or feature selection before vs. after splitting.

---

### Step 6: Modeling (M4, Days 4–12)
*M4 may begin on Day 4 using a grid-only stub table.*

* **Baselines:**
  * Heuristic rule: predict podium if $\text{grid} \le 3$.
  * Logistic Regression (standard statistical baseline).
* **Statistical Models:** Random Forest, Gradient Boosting (LightGBM or XGBoost) with class weighting.
* **Shallow Neural Network:** Keras implementation, 1–2 hidden layers (e.g., $64 \to 32$), dropout, early stopping monitoring validation PR-AUC, and class weighting.
* **Tuning & Thresholds:**
  * Hyperparameter search guided exclusively by validation set metrics.
  * Tune decision threshold to maximize validation $F_1$. **Test set remains untouched.**
* **Evaluation Metrics:**
  * Primary: **PR-AUC** (handles severe class imbalance, $\approx 15\%$ podium rate).
  * Secondary: **ROC-AUC** or **$F_1$**.
  * Report: ROC-AUC, PR-AUC, $F_1$, Precision, and Recall across Train, Validation, and Test sets.
* Require $\ge 3$ distinct modeling attempts: Logistic Regression $\to$ Random Forest $\to$ Tuned LightGBM $\to$ Shallow NN.

---

### Step 7: Ablation (M3, Days 11–13)
* Take the top-performing model and iteratively retrain it, holding out one feature group at a time via `FEATURE_GROUPS`.
* Report delta in validation and test PR-AUC using both a comparison table and a delta bar chart.

---

### Step 8: Explainable AI (XAI) (M2, Days 11–14)
* **Global Explanations:**
  * Permutation importance on the validation set.
  * SHAP summary/beeswarm plot (`TreeExplainer` for tree ensembles).
* **Local Explanations:**
  * SHAP waterfall plot and LIME breakdown for anomalous race outcomes (e.g., unexpected podium finisher or pole-sitter failing to podium).
* Interpret all plots explicitly; emphasize that feature importance does not imply causal inference.

---

### Step 9: Inference Function (M4, Days 12–14)
* Implement:
  ```python
  predict_podium(raceId, driverId, grid, quali_info=None)
  ```
  Dynamically aggregates historical pre-race features, executes the pre-fitted pipeline, and outputs predicted probabilities alongside the binary prediction.
* Demonstrate functionality on:
  1. A complete sample record.
  2. A record with missing values (e.g., absent qualifying session times) to verify proper imputation handling.

---

### Step 10: Integration and Report (All, Days 14–17)
* **Notebook Structure:**
  1. Setup & Configuration
  2. Data Audit
  3. Data Cleaning
  4. Exploratory Data Analysis (EDA)
  5. DE Questions (Q1–Q3)
  6. Feature Engineering & Validation
  7. Train/Val/Test Split & Preprocessing Pipelines
  8. Model Benchmarking & Tuning
  9. Feature Ablation Study
  10. Explainability (XAI)
  11. Inference Interface
  12. Limitations & Future Work
* Execute a complete, error-free **Run All** on Kaggle.
* **PDF Report Composition:**
  * DE Question findings and figures.
  * Feature registry with temporal validity proofs.
  * Master model evaluation table.
  * Ablation analysis and XAI visualizations.
  * Limitations: qualifying drift, technical regulation shifts, constructor rebrands, limited test volume.

---

## 4. Timeline

| Dates | Milestone |
| :--- | :--- |
| **Oct 6–7** | Kickoff, repo/Kaggle setup, shared config finalized, M1 ships cleaned dataset v0 |
| **Oct 8–10** | Parallel tracks: cleaning finalized, DE Q1–Q3, features v1, baseline models on stub |
| **Oct 11–12** | Feature freeze (Oct 12), split & preprocessing pipeline finalized |
| **Oct 13–14** | Complete model tuning, ablation study, XAI analysis, inference function |
| **Oct 15–16** | End-to-end integration, Kaggle Run All execution, code freeze |
| **Oct 17** | Final report polish, cross-training oral rehearsal |
| **Oct 18** | Submission buffer $\to$ **Submit (Kaggle link, GitHub link, PDF report)** |

### Cross-Training Rehearsal
To prepare for individual evaluation defenses, each member presents a 10-minute walkthrough of their section on **October 17**. Team members stress-test decisions with probing "why" questions to ensure universal project defense readiness.