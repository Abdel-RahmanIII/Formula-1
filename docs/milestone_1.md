# Milestone 1: Formula 1 Podium Prediction Companion

## Introduction

Formula 1 generates rich, relational race-weekend data—qualifying sessions, grid penalties, pit stops, driver and constructor histories—that determines, long before lights out, which drivers have a realistic shot at the podium. Predicting podium finishes from pre-race information is a domain where careful feature engineering and leakage control matter as much as model choice, since results, points, and status are only known after the race.

This project implements a full data-engineering and machine-learning pipeline: converting the raw relational F1 tables into a validated, leakage-safe analytical table, and predicting whether a driver will finish on the podium using only information available after qualifying and before the race starts.

---

## Dataset

* **Source:** [Formula 1 World Championship (1950–2024) – Kaggle / Ergast Dataset](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020)
* **Structure:** Relational dataset consisting of 14 interconnected CSV tables:
  * `circuits`
  * `constructors`
  * `constructor_results`
  * `constructor_standings`
  * `drivers`
  * `driver_standings`
  * `races`
  * `results`
  * `qualifying`
  * `lap_times`
  * `pit_stops`
  * `sprint_results`
  * `seasons`
  * `status`
* **Unit of Analysis:** One driver entering one race.
* **Prediction Target:** Whether that driver finishes on the podium (`positionOrder <= 3`).
* **Prediction Cutoff:** After qualifying, before race start. Current-race results, status, points, laps, pit stops, and post-race standings are strictly forbidden as features—using them constitutes **data leakage** (incorporating future information unavailable at prediction time). Identifying which fields constitute "future" information is a core learning objective.

---

## Project Objectives

### 1. Data Cleaning & Auditing

At minimum, your cleaning must address the following required checks (further exploration and handling of discovered anomalies is encouraged and must be documented):

* **Exploratory Data Analysis (EDA):**
  * Conduct EDA **both before and after** cleaning to demonstrate and quantify the impact of cleaning operations.
  * Every step must be supported with proper visualizations. Manual inspection alone is insufficient; choices must be justified programmatically and visually.
* **Sentinel Values & Semantic Typing:**
  * Clean placeholder missing values (e.g., literal string `\N`).
  * Apply semantic typing to dates and durations (e.g., convert date strings to datetime objects, lap-time strings to numeric seconds).
* **Grain & Duplicate Resolution:**
  * The modeling table must contain **exactly one row per driver per race**; the composite key `(raceId, driverId)` must be strictly unique.
  * Identify duplicates originating from early F1 history (primarily the 1950s) where shared drives took place (drivers swapping cars mid-race).
  * Define, document, and justify a deterministic rule for selecting which row to retain.
* **Integrity Constraints:**
  * Verify primary keys are unique and non-null.
  * Reconcile foreign key constraints using anti-joins to verify referential integrity (every foreign key must map to an existing parent row).
  * Raw CSV files must remain immutable; perform all operations on working copies.

---

### 2. Data-Engineering Questions

Answering each question requires multi-hop joins across tables (conclusions derived from `results.csv` alone are invalid). For each question, provide:
1. The analytical answer.
2. A supporting visualization.
3. A short justification of the grain, missingness handling, and pre-race temporal cutoff adherence.

#### Questions:
1. **Front-Row Conversion:** Which circuits convert a front-row start into a podium most often, and does that ranking change after the 2014 hybrid era? Distinguish qualifying position from grid position (which can deviate due to penalties).
2. **Home Advantage:** Do drivers podium more often when racing at a circuit in their home country than elsewhere, after controlling for starting position (i.e., comparing drivers who started from similar grid positions to decouple home advantage from qualifying performance)?
3. **Mechanical Retirements:** Which constructors have the highest mechanical-retirement rate in 2014–2021 vs. 2022–2024?
   * *Definition:* A mechanical retirement is a race start that terminated prematurely due to a failed car component, strictly excluding retirements caused by accidents, driver error, or regulatory/steward disqualifications.

---

### 3. Feature Selection & Engineering

* All feature selections must be backed by exploratory evidence (correlation matrices, distribution comparisons, or hypothesis-driven EDA). Keep all exploratory trials in the notebook for verification.
* Split the dataset appropriately into **Training, Validation, and Test** sets, providing a clear rationale for the chosen split boundary (e.g., temporal considerations).
* The precise feature set and categorical encodings are open to your design, provided each choice is documented and justified.

---

### 4. Predictive Modeling Task

Train and benchmark models on the identical analytical table (matching rows and feature spaces):
* **At least two distinct statistical ML models** (e.g., Logistic Regression, Random Forest, Gradient Boosting).
* **A shallow Neural Network** ($\approx 1\text{–}2$ hidden layers). Standard high-level libraries (e.g., Keras, PyTorch) are expected.
* **Formulation:** Binary classification ($\text{Podium} \in \{0, 1\}$).

#### Evaluation Metrics:
| Metric | What it measures |
| :--- | :--- |
| **ROC-AUC** | Area under the Receiver Operating Characteristic curve. Measures overall class separability. |
| **PR-AUC** | Area under the Precision-Recall curve. Evaluates retrieval ranking of rare positive instances (podiums $\approx 15\%$). More informative than ROC-AUC under class imbalance. |
| **$F_1$ Score** | Harmonic mean of precision and recall at a defined decision threshold, balancing false positives and false negatives. |

* Compute all metrics across Training, Validation, and unseen Test sets.
* Threshold calibration and hyperparameter tuning must be executed using training and validation data **only**—never the test set.

---

### 5. Experiments

* **Feature-Group Ablation:** Measure post-training marginal contributions by retraining the best-performing model while systematically dropping one feature group at a time (e.g., grid, qualifying, standings, form).
* **Preprocessing Order Experiments:** Run at least two controlled experiments testing the ordering or scope of preprocessing steps (e.g., fitting transformers on train-only vs. full data, impute-then-scale vs. scale-then-impute) and report before/after metric deltas.

---

### 6. Model Explainability (XAI)

* **Global Interpretability:** Permutation feature importance and SHAP summary/beeswarm analysis.
* **Local Interpretability:** Single-instance prediction explanations using LIME, local SHAP (waterfall/force plot), or both.
* **Causal Disclaimer:** Interpret all visualizations explicitly, documenting that statistical feature importance does **not** equal causal effect.

---

## Deliverables

1. **Run-All Jupyter Notebook:** Cleanly executed top-to-bottom containing audit, cleaning, data-engineering answers, features, models, ablation, XAI, and inference function.
2. **EDA Artifacts:** Comprehensive pre- and post-cleaning plots and analysis.
3. **Analytical Modeling Table:** Exactly one row per `(raceId, driverId)` with leakage-safe features.
4. **Model Comparison Table:** All metrics reported across train/validation/test splits, including justification of primary vs. secondary metrics.
5. **Experimental Results:** Ablation table/charts and at least two preprocessing-order experiments.
6. **XAI Suite:** Global and local interpretation figures with written analyses.
7. **Inference Function:** Functional implementation demonstrated on both complete and partially-missing records.
8. **Structured Analytical Report (PDF):**
   * Written answers and figures for the three DE questions.
   * Feature registry with temporal validity proofs.
   * Model evaluation benchmarks.
   * Documented limitations (e.g., historical qualifying-drift, era boundary shifts).

---

## Evaluation Expectations

1. **Individual Defense Readiness:** Every team member must be prepared to defend any stage of the pipeline (cleaning, engineering, modeling, or evaluation metric choices).
2. **Contextual Justification:** Ground all technical decisions in empirical data or hypothesis-driven EDA; "an AI tool suggested it" is not an acceptable justification.
3. **Visible Comparisons:** Keep comparative trials and baselines organized in distinct notebook sections to display clear before-and-after evidence.
4. **Baseline Requirements:** Include a trivial heuristic or simple statistical baseline (e.g., logistic regression) to verify that model complexity is justified.

---

## Milestone 1 Checklist

- [ ] **Exploratory Data Analysis (EDA)**
  - [ ] Pre-cleaning visualizations and summary statistics
  - [ ] Post-cleaning comparison visualizations
- [ ] **Data Cleaning**
  - [ ] Sentinel value handling (`\N`) and semantic type casting
  - [ ] Enforce grain: unique `(raceId, driverId)` with documented duplicate resolution
  - [ ] Primary key and foreign key referential integrity validation
- [ ] **Data-Engineering Questions (Q1–Q3)**
  - [ ] Multi-hop joins executed with correct pre-race cutoffs
  - [ ] Clear visualizations generated for each question
  - [ ] Written answers with grain and missingness justification (Notebook & Report)
- [ ] **Feature Selection & Engineering**
  - [ ] Evidence-backed feature selection (plots, correlations, experiments)
  - [ ] Strict temporal leakage prevention (historical rolling/expanding windows only)
- [ ] **Preprocessing & Splitting**
  - [ ] Justified temporal train/validation/test split
  - [ ] Distribution shift plots before and after preprocessing
  - [ ] At least two preprocessing-order experiments reported
- [ ] **Predictive Modeling**
  - [ ] Baseline statistical model implemented
  - [ ] Alternative statistical model implemented
  - [ ] Shallow Feedforward Neural Network (FFNN) implemented
  - [ ] Threshold tuning on validation set only
  - [ ] Complete evaluation metric suite reported across all splits
- [ ] **Ablation & Interpretability (XAI)**
  - [ ] Feature-group ablation study executed and visualized
  - [ ] Global explainability (Permutation Importance, SHAP beeswarm)
  - [ ] Local explainability (LIME / SHAP waterfall)
  - [ ] Causal vs. predictive distinction explicitly stated
- [ ] **Operationalization**
  - [ ] Inference function supporting complete and missing-data records
  - [ ] Complete notebook successfully executes "Run All" top to bottom

---

## Submission Details

* **Deadline:** 18 October 2026 at 11:59 PM
* **Submission Portal:** [Google Form Submission Link](https://forms.gle/esDxHsvfzffYHVAZ9)
* **Required Links & Files:**
  1. Accessible link to Kaggle notebook
  2. Accessible GitHub repository link
  3. Final analytical report in PDF format