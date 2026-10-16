# Milestone 1 (MS1) — Piazza Q&A & Project Decisions Summary

---

## 1. Golden Rule Across All Decisions
> **Core Instructor Principle:** Many preprocessing, feature engineering, and modeling decisions are up to you ("designer choice"), **provided they are backed by valid reasoning, EDA, or experimental evidence**—never "gut feeling" or convenience. However, certain hard constraints ( listed below) are strictly enforced.

---

## 2. Quick Reference: Hard Rules vs. Designer Choices

| Topic | Verdict | Summary of Rule / Action |
| :--- | :--- | :--- |
| **Dropping Old Historical Eras (e.g., pre-2003 / pre-2006)** | **STRICT NO** | You **must** utilize the entire dataset. Do not truncate old eras due to regulation changes/concept drift (this will be addressed in MS2). |
| **Leaving Nulls Unhandled** | **AVOID** | Leaving nulls can hurt your model. Experiment with imputation methods vs. dropping columns/rows and justify with results. |
| **Encoding `grid == 0` as `last_grid_position + 1`** | **APPROVED** | Explicitly approved so the model understands pit-lane/0 starts are worse than P1. |
| **Removing `positionText == 'F'` (Did Not Qualify)** | **APPROVED** | Allowed because failing to qualify is known **before** the race starts. |
| **Removing `positionText == 'W'` (Withdrawn)** | **CONDITIONAL** | Instructor #1 said only remove `'F'`. Instructor #2 said removing `'W'` is a design choice **only if** you prove via experiments that keeping vs. removing yields the same results. |
| **Duplicate Drivers: Combining Pre-Race of Driver A + Post-Race of Driver B** | **DATA LEAKAGE** | Using post-race outcomes to reconstruct/stitch pre-race entries causes data leakage. |
| **Duplicate Drivers: Using the Car the Driver Finished In** | **APPROVED** | Does **not** violate the post-race information cut-off. |
| **DE Q1: Grid vs. Qualifying Conversion Rates** | **GRID ONLY** | Only show conversion rates for **grid starting position**. The prompt's note just reminds you that `grid != qualifying` due to penalties. |
| **DE Q3: Mechanical Retirements Classification** | **EXPLICIT RULE** | `Puncture`, `Tyre`, `Tyre puncture`, `Fire`, and `Safety belt` = **Mechanical**. `Refuelling` = **NOT Mechanical**. |
| **Linear Regression as Baseline** | **INVALID** | Linear regression is not suited for classification tasks. Do not intentionally build an artificially terrible baseline just to make your main model look good. |
| **Deliverables Format** | **REQUIRED** | Submit **both** the Jupyter Notebook and a Report exported as **PDF** (written in LaTeX or Word). |

---

## 3. Detailed Categorized Q&A Breakdown

### A. Historical Data Range & Missing Era Data (`qualifying.csv` from 1994)

* **Q: Can we drop old data and start the dataset from 2003 or 2006 (due to F1 regulation changes, qualifying format changes, and concept drift)?**
  * **Instructor Answer (Farida Helmy):** **No.** Restricting the dataset and discarding a large portion of historical data is not allowed. You must find a way to utilize the entire dataset to see if the model can generalize across rule changes. Concept drift appears in later years as well, and this specific angle will be addressed in the upcoming milestone.
* **Q: `qualifying.csv` starts from the mid-1990s (1994). Do we drop the missing values, keep them, or exclude the pre-1994 era across all datasets?**
  * **Instructor Answer (Mayar Osama / Farida Helmy / Salma Kishk):** Whether you drop or impute missing qualifying values is a designer choice that depends on how you split and handle your data, and you must be able to defend it. *(Note: Keep in mind the strict rule above against dropping entire historical eras like pre-2003/2006 when training your model).*
* **Q: Should we fill in every missing (null) value in the dataset, or is it acceptable to leave some values as null (e.g., columns with >60% missing values)?**
  * **Instructor Answer (Salma Kishk):** Leaving values as null can negatively impact your model. You must experiment thoroughly to decide whether the best course of action is **imputation** (and which method) or **dropping** (and which columns/rows). Every decision requires an evidence-based justification.

---

### B. Duplicate Drivers, Shared Cars (1950s), & Row Filtering (`F`, `W`, `R`, `E`, `D`)

* **Q: Regarding duplicate drivers in the 1950s (where drivers shared/swapped cars), should we completely remove the duplicates or keep one of them?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):** It is up to you, provided you justify your choice.
* **Q: For duplicate drivers in a race, is considering the car the driver finished in (instead of the car they started with) considered a violation of the post-race info cut-off?**
  * **Instructor Answer (Mayar Osama):** **No**, it does not violate the post-race cut-off.
* **Q: For duplicate drivers, can we take the pre-race info of the first driver (who started the race) and combine it with the post-race result of the second driver (who took over mid-race)?**
  * **Instructor Answer (Salma Kishk):** Using information received after a race is complete to fill/stitch issues in pre-race data will cause **data leakage**.
* **Q: Can we exclude rows where `positionText == 'F'` (Did Not Qualify), while keeping `'W'` (Withdrawn), `'R'` (Retired), `'E'` (Excluded), and `'D'` (Disqualified)?**
  * **Instructor Answer (Mayar Osama):** **Yes**, you may remove `'F'` rows because failing to qualify is known before the race starts. (`'R'`, `'E'`, `'D'` are strictly post-race outcomes).
* **Q: Can we also remove `'W'` (Withdrawn) rows since they don't carry predictive race info?**
  * **Instructor Answer (Farida Helmy):** That is a design choice that you **must justify through experiments**. If you believe removing `'W'` is valid, you must showcase experimentally that keeping vs. removing it yields the same results.

---

### C. Feature Engineering, Data Leakage & Encoding

* **Q: Is it okay to encode `grid == 0` in the modeling table as `last_grid_position + 1` in that race so the model understands it is worse than P1?**
  * **Instructor Answer (Farida Helmy):** **Yes**, that is approved.
* **Q: When a constructor/team name changes, do we use its previous name’s history for the new team name?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):** It depends on how you merge and structure your data; justify your approach.
* **Q: What does "leakage judgment call" mean regarding Sprint races?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):** You need to explore and decide whether including Sprint results creates a data leakage problem or not, explain your reasoning, and decide how to handle/fix it.
* **Q: The domain background mentions tyre compounds, but they are not in our dataset features. Do we need to include them?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):** **No.** If a feature is not in the provided dataset, you do not need to include it.
* **Q: Do we justify chosen features using pre-training EDA or post-split training outputs?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):** You can (and should) use **both**. EDA is a great initial step to justify including/excluding features, though sometimes a feature that looks weak in EDA still impacts model performance. Back your choices with evidence from EDA and/or model experiments.

---

### D. Data Engineering Specific Questions (Q1 & Q3)

* **Q (Data Engineering Q1): The prompt says *"Distinguish qualifying position from grid (which can differ due to penalties)."* Do we need to show conversion rates for both grid and qualifying positions?**
  * **Instructor Answer (Farida Helmy):** **No.** What matters in this question is the **grid starting position**, not the qualifying position. The note is simply a reminder that the two columns do not map 1-to-1 because penalties affect the starting grid.
* **Q (Data Engineering Q3): Do the retirement types `{"Puncture", "Tyre", "Tyre puncture", "Fire", "Safety belt", "Refuelling"}` fall under "Mechanical" retirements?**
  * **Instructor Answer (Farida Helmy):** For simplicity, consider **all of them as Mechanical retirements EXCEPT `"Refuelling"`**.
    * **Mechanical:** `Puncture`, `Tyre`, `Tyre puncture`, `Fire`, `Safety belt`
    * **Not Mechanical:** `Refuelling`

---

### E. Data Splitting & Modeling Baselines

* **Q: Do the train/val/test split boundaries have to be split by time, and do we have to use `train <= 2019` as mentioned in the intro?**
  * **Instructor Answer (Salma Kishk & Farida Helmy):** The `train <= 2019` split in the intro was just a naive example. How you split the data (and whether you compare different splits) is up to you, **as long as you have valid reasoning and strictly prevent data leakage** (e.g., future information leaking into past predictions).
* **Q: Is Linear Regression considered a proper baseline, or a Neural Network with 1 hidden layer and a small number of neurons?**
  * **Instructor Answer (Farida Helmy & Salma Kishk):**
    1. **Linear Regression is NOT suited for classification tasks** (do not use it for classification).
    2. For a small Neural Network baseline, you **cannot** purposely build an overly bad/shallow/broken model just to get poor baseline metrics and make your main architecture look good by comparison. Your baseline must be a genuine, reasonable baseline, and you must properly improve upon it.
* **Q: Can we use ResNet50 to compare with our baseline models?**
  * **Instructor Answer (Salma Kishk):** ResNet50 is primarily designed for image/computer vision tasks. Doing something extra doesn't hurt, but you will be questioned on it and must justify **why** you used a vision architecture on tabular data over traditional approaches and **how** you adapted it.

---

### F. Deliverables & Submission

* **Q: Should the report be in Word, LaTeX, or just inside the Jupyter Notebook?**
  * **Instructor Answer (Salma Kishk):** A separate report is **required alongside the notebook**. Both Word and LaTeX are accepted, but the final report **must be exported and submitted as a PDF**.