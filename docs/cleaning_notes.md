# Formula 1 Data Cleaning & Contract Compliance Notes

> **Target Audience:** Pipeline Engineer / Data Lead (**M1**) executing **Step 1 (Audit)** and **Step 2 (Data Cleaning)**.  
> **Goal:** Ensure all cleaned tables and the downstream analytical table strictly satisfy the **Modeling Data Contract** ([DEC-005](file:///d:/GUC/Semester%209/ACL/Project/Formula%201/docs/decision_log.md#L15)) and pass programmatic validation without data leakage.

---

## 1. 14-Table Structural Reference & Memory Footprint

The raw dataset consists of 14 relational tables loaded from `archive/`. Below is the verified physical inventory from the initial data audit:

| Table | CSV File | Rows | Cols | Memory | Primary Key / Composite Grain | Temporal Safety Classification |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **`circuits`** | `circuits.csv` | 77 | 9 | 5.5 KB | `circuitId` | **Pre-Race Safe** (static circuit metadata) |
| **`constructors`** | `constructors.csv` | 212 | 5 | 8.4 KB | `constructorId` | **Pre-Race Safe** (static team metadata) |
| **`drivers`** | `drivers.csv` | 861 | 9 | 60.7 KB | `driverId` | **Pre-Race Safe** (static driver demographics) |
| **`seasons`** | `seasons.csv` | 75 | 2 | 1.3 KB | `year` | **Pre-Race Safe** (calendar year metadata) |
| **`races`** | `races.csv` | 1,125 | 18 | 158.3 KB | `raceId` | **Pre-Race Safe** (scheduled race calendar) |
| **`qualifying`** | `qualifying.csv` | 10,494 | 9 | 738.0 KB | `qualifyId` / `(raceId, driverId)` | **Pre-Race Safe** *(Requires column renaming)* |
| **`results`** | `results.csv` | 26,759 | 18 | 3.7 MB | `resultId` / `(raceId, driverId)`* | **Hybrid / Leakage Core** *(Target + 11 blacklisted cols)* |
| **`sprint_results`**| `sprint_results.csv` | 360 | 16 | 45.1 KB | `resultId` / `(raceId, driverId)` | **Conditional Pre-Race** *(Requires `sprint_` prefix)* |
| **`status`** | `status.csv` | 139 | 2 | 2.3 KB | `statusId` | **Post-Race Leakage** (forbidden for race $t$) |
| **`constructor_results`** | `constructor_results.csv`| 12,625 | 5 | 493.3 KB | `constructorResultsId` | **Post-Race Leakage** (points/status for race $t$) |
| **`constructor_standings`** | `constructor_standings.csv`| 13,391 | 7 | 732.4 KB | `constructorStandingsId` | **Ergast Trap** (recorded *after* race $t$) |
| **`driver_standings`** | `driver_standings.csv` | 34,863 | 7 | 1.9 MB | `driverStandingsId` | **Ergast Trap** (recorded *after* race $t$) |
| **`lap_times`** | `lap_times.csv` | 589,081 | 6 | 27.0 MB | `(raceId, driverId, lap)` | **In-Race Telemetry (100% Forbidden)** |
| **`pit_stops`** | `pit_stops.csv` | 11,371 | 7 | 622.0 KB | `(raceId, driverId, stop)` | **In-Race Events (100% Forbidden)** |

*\* Note on `results.csv`: Contains 176 duplicate `(raceId, driverId)` rows in raw form due to historical shared drives.*

---

## 2. Core Contracts the Cleaner Must Satisfy

When assembling the clean dataset and modeling table, your output must pass [`validate_data_contract()`](file:///d:/GUC/Semester%209/ACL/Project/Formula%201/formula-1.ipynb#L394-L442):

1. **Table Grain:** Strictly one row per `(raceId, driverId)`.
   ```python
   assert df.duplicated(subset=['raceId', 'driverId']).sum() == 0
   ```
2. **Identifier Non-Nullity:** The 5 lineage columns must exist and contain **0 NULLs**:
   - `raceId` (`int64`)
   - `driverId` (`int64`)
   - `constructorId` (`int64`)
   - `date` (`datetime64[ns]` or ISO date string)
   - `year` (`int64`)
3. **Binary Target:** Column `podium` must exist, have **0 NULLs**, and values strictly in `{0, 1}`:
   ```python
   df['podium'] = (df['positionOrder'] <= 3).astype(int)
   ```
4. **Leakage Blacklist Compliance:** Feature columns must not contain any column matching `LEAKAGE_BLACKLIST_COLUMNS` or `LEAKAGE_PATTERNS`.
5. **Clean Working Copy Rule:** Keep `raw_dataframes` completely immutable. Perform all cleaning operations on `.copy()`.

---

## 3. Critical Traps & Gotchas (MUST NOT MISS)

### ⚠️ Trap 1: The Historical Shared-Drive Grain Violation (176 Duplicates)
* **What happens:** Raw `results.csv` contains **26,759 rows**, but only **26,668 unique `(raceId, driverId)` pairs** (176 duplicate rows).
* **Why it happens:** In 1950–1978 (predominantly 1953–1956), drivers who retired frequently took over a teammate's car mid-race, or teams entered multiple cars under one driver.
* **The danger:** If merged as-is, `validate_data_contract()` will throw:
  `AssertionError: Grain violation: Found 176 duplicate (raceId, driverId) rows!`
* **Required Cleaning Action:** Apply a deterministic deduplication rule before validating:
  ```python
  # Sort so that the car the driver actually started (grid > 0) and best finish comes first
  results_clean = (
      results_copy
      .assign(started_on_grid=lambda d: d['grid'] > 0)
      .sort_values(by=['raceId', 'driverId', 'started_on_grid', 'positionOrder'], ascending=[True, True, False, True])
      .drop_duplicates(subset=['raceId', 'driverId'], keep='first')
      .drop(columns=['started_on_grid'])
  )
  ```
* Document the rule and number of dropped rows in [decision_log.md](file:///d:/GUC/Semester%209/ACL/Project/Formula%201/docs/decision_log.md).

---

### ⚠️ Trap 2: Column Collision on `qualifying.position`
* **What happens:** In `qualifying.csv`, the column recording qualifying rank is named `position` (`int64`).
* **The danger:** In `results.csv`, `position` is the race finishing position (which is blacklisted for leakage). If `qualifying` is merged without renaming, `assert_leakage_safe()` will catch `position` and crash the pipeline.
* **Required Cleaning Action:** Immediately rename before joining:
  ```python
  qualifying_clean = qualifying_copy.rename(columns={'position': 'quali_position'})
  ```

---

### ⚠️ Trap 3: `sprint_results.csv` Target & Blacklist Collisions
* **What happens:** Sprints run on Saturday *before* Sunday's Grand Prix, making them legally pre-race for Sunday's prediction. However, `sprint_results.csv` uses identical column names as `results.csv` (`position`, `positionText`, `positionOrder`, `points`, `milliseconds`, `statusId`).
* **The danger:** Merging raw sprint columns will overwrite the Sunday target (`positionOrder`) or trigger direct blacklist violations.
* **Required Cleaning Action:** Prefix all sprint metrics:
  ```python
  sprint_clean = sprint_results_copy.rename(
      columns=lambda col: f"sprint_{col}" if col not in ['raceId', 'driverId'] else col
  )
  ```
  Retain only safe pre-race sprint features: `sprint_position`, `sprint_points`.

---

### ⚠️ Trap 4: The "Ergast Trap" in Standings Tables
* **What happens:** In `driver_standings.csv` and `constructor_standings.csv`, records associated with `raceId = R` reflect points and standings **after race $R$ has concluded**.
* **The danger:** Joining on `raceId` leaks the outcome of the race being predicted!
* **Required Cleaning Action:**
  1. Standings must be strictly **lagged to round $t-1$** within each championship season.
  2. For Round 1 of any season, pre-race points and wins must be set to `0`, and pre-race rank set to a sentinel or baseline (e.g., previous season's finish or `None`/imputed).
  3. Rename columns to avoid collisions: `driver_pre_race_points`, `driver_pre_race_rank`, `constructor_pre_race_points`, `constructor_pre_race_rank`.

---

### ⚠️ Trap 5: Sentinel Values (`\N`) and Object Dtype Pollution
* **What happens:** In raw Ergast CSVs, missing values are encoded as string `\N`.
* **The danger:** Numeric columns get coerced into Pandas `object` dtype (e.g., `results.fastestLap`, `results.milliseconds`, `drivers.number`, `qualifying.q1`). Mathematical operations and models will fail.
* **Required Cleaning Action:**
  1. Pass `na_values=[r'\N', r'\\N', '']` when reading CSVs (already implemented in `load_raw_datasets`).
  2. Cast numeric columns explicitly:
     - `results['positionOrder']`: ensure `int64`.
     - `results['grid']`: ensure `int64`.
     - `drivers['dob']`: parse with `pd.to_datetime(drivers['dob'])`.
     - `races['date']`: parse with `pd.to_datetime(races['date'])`.
     - Time strings (e.g. `q1`, `q2`, `q3` formatted as `"1:24.312"`): parse into float seconds:
       ```python
       def lap_time_to_seconds(time_str):
           if pd.isna(time_str) or not isinstance(time_str, str) or ':' not in time_str:
               return np.nan
           mins, secs = time_str.split(':')
           return float(mins) * 60.0 + float(secs)
       ```

---

### ⚠️ Trap 6: Pit-Lane Starts Encoded as `grid = 0`
* **What happens:** In modern Formula 1, cars starting from the pit lane (due to parc fermé violations or power unit changes) are assigned `grid = 0` in Ergast.
* **The danger:** A model treating `grid` as an ordinal integer would interpret `0` as better than pole position (`1`), severely distorting coefficients and trees.
* **Required Cleaning Action:**
  1. Create a binary indicator: `df['pit_start'] = (df['grid'] == 0).astype(int)`.
  2. Recode `grid = 0` to back-of-the-grid (e.g., `field_size` or max grid position for that race).

---

### ⚠️ Trap 7: Non-Starter Entrants (DNQ / DNPQ / DNS)
* **What happens:** Historical races often had more entrants than grid slots. Drivers who Did Not Qualify (`DNQ`), Did Not Pre-Qualify (`DNPQ`), or Did Not Start (`DNS`) appear in `results.csv`.
* **The danger:** At prediction cutoff (after qualifying, before race start), we know these drivers are not on the grid and cannot finish on the podium.
* **Required Cleaning Action:**
  - Verify `positionText` for non-starters (`'D'`, `'W'`, `'F'`) or filter to confirmed starters (`grid > 0` or verified pit-lane starters). Document the exact filter in [decision_log.md](file:///d:/GUC/Semester%209/ACL/Project/Formula%201/docs/decision_log.md).

---

### ⚠️ Trap 8: Era Drift & Knockout Qualifying Missingness
* **What happens:**
  - `qualifying.csv` only starts in **1994** (10,494 rows vs 26,759 in `results`).
  - Knockout Q1/Q2/Q3 format only began in **2006**.
  - In Q1/Q2/Q3, missing values in `q2` and `q3` are **structurally expected** (eliminated drivers do not participate in later sessions).
* **The danger:** Dropping rows with `NaN` in `q2`/`q3` would discard 50%+ of all modern drivers!
* **Required Cleaning Action:**
  1. Do not drop rows for missing `q2`/`q3`.
  2. Construct informative indicator features:
     - `q3_reached = df['q3'].notna().astype(int)`
     - `missing_quali_flag = df['quali_position'].isna().astype(int)`
  3. Fall back to `results.grid` for starting position across historical eras where `quali_position` is absent.

---

### ⚠️ Trap 9: Indianapolis 500 Scope Exclusion ([DEC-003](file:///d:/GUC/Semester%209/ACL/Project/Formula%201/docs/decision_log.md#L13))
* **What happens:** From 1950 to 1960, the Indianapolis 500 was officially counted as a round of the F1 World Championship, but was run under AAA/USAC Champ Car oval rules with non-F1 constructors and American dirt-track specialists.
* **Required Cleaning Action:**
  - Filter out Indy 500 races when building the F1 modeling set:
    ```python
    if EXCLUDE_INDY_500:
        indy_mask = (df['year'].between(1950, 1960)) & (df['name'].str.contains('Indianapolis 500', case=False, na=False))
        df = df[~indy_mask]
    ```

---

## 4. End-of-Cleaning Validation Checklist

Before handing off the cleaned dataset to **M2 (Analytics)** and **M3 (Features)**, run this self-check script in your notebook:

```python
# 1. Validate composite grain
assert clean_df.duplicated(subset=['raceId', 'driverId']).sum() == 0, "Duplicate (raceId, driverId) found!"

# 2. Validate identifier non-nullity
for col in ['raceId', 'driverId', 'constructorId', 'date', 'year']:
    assert col in clean_df.columns, f"Missing identifier column: {col}"
    assert clean_df[col].isnull().sum() == 0, f"Nulls found in identifier: {col}"

# 3. Validate target column
assert 'podium' in clean_df.columns, "Target 'podium' missing!"
assert clean_df['podium'].isnull().sum() == 0, "Nulls found in target!"
assert set(clean_df['podium'].unique()).issubset({0, 1}), "Target is not binary {0, 1}!"

# 4. Validate sentinel eradication
assert not (clean_df.astype(str) == r"\N").any().any(), "Literal string '\\N' remains in cleaned dataset!"

# 5. Full data contract & leakage check
from shared import validate_data_contract
validate_data_contract(clean_df, feature_cols=candidate_features)
print(" All cleaning validations passed successfully!")
```
