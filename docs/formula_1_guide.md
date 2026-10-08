# Formula 1 for Newcomers: An Introduction to the Podium Prediction Project

Our model predicts, for every driver in a race, whether they finish in the top 3 (the podium), using only what is known after qualifying and before the race starts. To judge features, spot leakage, and explain results, every team member needs a working mental model of how Formula 1 works and how its rules shifted between 1950 and 2024.

Formula 1 is a world championship of single-seat racing cars, run every year since 1950. Each year is a season made of individual races (officially Grands Prix, e.g., the British Grand Prix), held at different circuits around the world.

Drivers are the people in the cars. Constructors are the teams that build and run the cars (Ferrari, McLaren, Mercedes, Red Bull). Today each constructor enters exactly two cars, so a modern race has about 20 drivers. In the 1950s to 1980s fields were much larger and far less uniform.

There are two championships each season, both decided by points:

* **Drivers' Championship:** Points go to the individual driver.
* **Constructors' Championship (since 1958):** Points of a team's cars are added together.

A **podium** is a finish in 1st, 2nd, or 3rd place, named after the stand where the top three receive trophies. Podiums are rare by design: about 3 of 20 drivers per race, so roughly 15% of rows in the modern era and far less in eras with 30+ entrants.

What decides who wins is a mix of car performance (the dominant factor in most eras), driver skill, starting position, strategy, reliability, and luck. That is why our features lean on grid position and constructor form, not just driver form.

---

## The Race Weekend

A modern race weekend runs Friday to Sunday, and our prediction is made in the gap between the grid being fixed and the lights going out.

```
[ Practice ] ───> [ Qualifying ] ───> [ Starting Grid ] ───┬───> [ Race ] ───> [ Results ]
Setup runs;       Timed laps          Quali order          │     ~305 km;      Positions,
no points;        decide the          plus penalties       │     top 3         points, status,
not in dataset    starting order      and pit starts       │     make podium   standings
                                                           │
◀────────────────── PRE-RACE CUTOFF ───────────────────────┼─────────────────────────────▶
         Known before lights out: USABLE AS FEATURES       │  Known only after: TARGET
```

1. **Practice (Friday, sometimes Saturday):** Free sessions where teams tune the car. No points, and not in the Kaggle dataset.
2. **Qualifying (usually Saturday):** Each driver sets timed laps. The fastest takes pole position (P1 on the grid); P1 and P2 form the front row.
3. **Starting Grid:** Normally the qualifying order, but it can change. Penalties move drivers back (e.g., for fitting more engine or gearbox parts than allowed, or for an offence at an earlier race). A driver can also start from the pit lane or be excluded from qualifying. So qualifying position and grid position are not the same thing.
4. **Race (Sunday):** A standing start from the grid, about 305 km (Monaco is shorter) with a time limit. Drivers make pit stops for fresh tyres. The first three across the line finish on the podium.
5. **Results:** Finishing order, points, the reason anyone stopped early (`status`), and updated championship standings. All of this is post-race.

### Sprint Weekends
Sprint weekends (2021 onward, a handful of races per season) add a short Saturday race of about 100 km with fewer points. The format kept changing:
* In 2021–2022, the sprint result set the Sunday grid.
* From 2023 onward, Friday qualifying sets the Sunday grid, and a separate sprint qualifying sets the sprint grid.

Because the sprint runs before the main race, its result is technically pre-race information.

---

## Glossary

These are the terms that come up in the dataset, the milestone brief, and our discussions, sorted alphabetically:

| Term | Meaning | Where it matters for us |
| :--- | :--- | :--- |
| **Classified** | A driver who completed enough of the race distance (today 90% of the winner's laps) to be given an official position, even if they stopped before the end. | Explains why some retired drivers still have a numeric position. |
| **Constructor** | The team that builds and enters the car; can change name when sold (e.g., Toleman became Benetton, then Renault, Lotus, Alpine). | Each name is a separate `constructorId`, so team history can break at renames. |
| **DNF** | Did Not Finish: the car stopped before the end (crash, mechanical failure, etc.). | `status` table; Question 3 on mechanical retirements. |
| **DNQ / DNPQ** | Did Not (Pre-)Qualify: too slow to earn a grid slot in eras with more entrants than grid places. | Rows with no race start; decide whether they belong in the modeling table. |
| **DRS** | Drag Reduction System, a rear-wing flap that eases overtaking, introduced in 2011. | Makes grid position slightly less decisive after 2011. |
| **DSQ** | Disqualified after the race, usually for a technical or sporting breach. | Result changes after the chequered flag; still post-race. |
| **Fastest lap** | The quickest single lap in the race; worth a bonus point in some eras. | Post-race; never a feature. |
| **Front row** | Grid positions 1 and 2. | Question 1. |
| **Grand Prix** | Formal name of a race event. | Race names in `races.csv`. |
| **Grid position** | Where the car actually starts the race, after penalties. | Allowed feature; `0` in the data means a pit-lane start (verify in EDA). |
| **Home race** | A race held in the driver's own country. | Question 2; needs mapping driver nationality (e.g., "British") to circuit country (e.g., "UK"). |
| **Hybrid era** | 2014–2021 rules: 1.6-litre turbo V6 engines with energy recovery. | Question 1 and 3 era split. |
| **Lapped** | Finished but one or more laps behind the winner; status shows "+1 Lap", etc. | Counts as finished, not a retirement. |
| **Pit stop** | A stop in the pit lane to change tyres (and in some eras, refuel). | Post-race data; never a feature. |
| **Pole position**| First place on the starting grid, earned by the fastest qualifying lap. | Strongest single predictor of a podium. |
| **Podium** | Finishing 1st, 2nd, or 3rd. | Our target: $\text{positionOrder} \le 3$. |
| **Qualifying** | Timed session that sets the starting order. | Allowed feature; coverage in the data is patchy for older years. |
| **Retirement** | Same as DNF; split into mechanical (engine, gearbox, hydraulics) and accident/driver causes. | Question 3 needs a mechanical vs. non-mechanical grouping of `status` values. |
| **Safety car** | A road car that neutralises the race after an incident, bunching up the field. | Reason upsets happen; not a feature. |
| **Season** | One championship year. | Split boundaries: train $\le 2019$, validation $2020\text{–}2021$, test $\ge 2022$. |
| **Sprint** | Short Saturday race on selected weekends since 2021. | `sprint_results.csv`; a leakage judgement call. |
| **Standings** | Cumulative championship points and rank after each race. | Must be shifted to "standings before this race" to be leakage-safe. |
| **Status** | Why a driver's race ended: "Finished", "+1 Lap", "Engine", "Collision", etc. | Post-race; used for Question 3 only. |
| **Tyre compounds** | Softer tyres are faster but wear quicker; since 2007 each driver must use two dry compounds in a dry race. | Background for strategy; not in our features. |

---

## How a Result is Recorded

Every driver who enters a race gets a row in `results.csv`, and three different "position" columns describe where they ended up. Our target uses `positionOrder` because it is the only one filled for every row.

| Column | What it holds | Example for a driver who crashed out |
| :--- | :--- | :--- |
| `position` | Official finishing position; empty (`\N`) if not classified | `\N` |
| `positionText` | Position as text, or a letter code when there is no position | `R` |
| `positionOrder` | A full ranking of every entrant, classified or not; always filled | `17` |

The letter codes in `positionText` are:
* **R:** Retired
* **D:** Disqualified
* **E:** Excluded
* **W:** Withdrawn
* **F:** Failed to qualify
* **N:** Not classified

A retired driver can still be "classified" and receive a numeric position if they completed 90% of the winner's race distance.

The `status` column (via `status.csv`) describes why a driver's race ended. `"Finished"`, `"+1 Lap"`, `"+2 Laps"`, etc., mean the driver reached the chequered flag. Everything else is a reason for stopping, and there are over 100 distinct status values. For Question 3, group them into:
* **Mechanical failures:** Engine, Gearbox, Hydraulics, Brakes, Power Unit, etc.
* **Non-mechanical causes:** Accidents, driver errors, regulatory decisions, etc.

*Note on Podiums:* A podium finish is almost always a clean finish on the lead lap, but a post-race disqualification can promote the 4th-place car. `positionOrder` already reflects the final, post-appeal classification.

---

## Qualifying Formats Through History

Qualifying has always ranked drivers by lap time, but the format shifted repeatedly, and the dataset only records it in detail for recent decades. For most of F1 history, the `grid` column in `results.csv` is our only record of starting order.

| Seasons | Format | What the dataset shows |
| :--- | :--- | :--- |
| **2006–2024** | Three-part knockout: Q1 drops the slowest cars, Q2 drops more, Q3 decides the top 10 (a failed "elimination" variant was tried for two races in 2016). | `q1`, `q2`, `q3` lap times; drivers knocked out early have `\N` for later sessions. |
| **2005** | Single-lap runs, briefly as an aggregate of two sessions. | Mostly `q1` only. |
| **2003–2004** | Single-lap, one car on track at a time. | Mostly `q1` only. |
| **1996–2002** | One-hour session, 12-lap limit, best lap counts; the "107% rule" excluded drivers too far off pole. | Mostly `q1` only. |
| **1950–1995** | Varied: usually timed sessions on Friday and Saturday with best time counting; pre-qualifying for oversubscribed fields in late 1980s / early 1990s. | Little or no qualifying data. |

> **Why this matters:** The milestone brief warns about **"historical qualifying-coverage drift"**. Qualifying-based features will be missing for most pre-2000s rows. Our EDA should plot qualifying coverage per season and decide whether to impute, fall back to `grid`, or restrict the training window. Confirm the exact starting year of `qualifying.csv` in your dataset copy.

---

## Technical and Sporting Eras (1950–2024)

F1 rewrites its technical regulations every few years, reshuffling which teams are competitive:

| Era | What defined it | Who tended to win |
| :--- | :--- | :--- |
| **2022–2024: Ground-effect era** | New cars generating grip from shaped floor tunnels for closer racing; team budget cap enforced since 2021. | Red Bull dominant in 2022–2023; McLaren won the 2024 constructors' title. |
| **2014–2021: Turbo-hybrid era** | 1.6-litre turbo V6 engines with energy recovery; wider, faster cars from 2017; COVID-shortened 17-race season in 2020. | Mercedes won every constructors' title; Verstappen (Red Bull) won 2021 drivers' title. |
| **2009–2013: Late V8 era** | Aerodynamic reset in 2009; refuelling banned from 2010; DRS and single tyre supplier (Pirelli) introduced in 2011. | Brawn in 2009, then Red Bull and Vettel from 2010–2013. |
| **1995–2008: V10 and early V8** | 3-litre V10s (V8s from 2006); in-race refuelling allowed 1994–2009, making pit strategy critical. | Williams, McLaren, then Ferrari and Schumacher dominant (2000–2004). |
| **1989–1994: Post-turbo** | Turbos banned; electronic driver aids flourished, then banned for 1994; safety car formalised in 1993. | McLaren-Honda, then Williams-Renault. |
| **1977–1988: Turbo & ground effect** | Turbocharged engines from 1977; early ground-effect cars until flat floors mandated in 1983; refuelling banned from 1984. | McLaren and Williams strong across the 1980s. |
| **1966–1976: 3-litre & wings** | Engine displacement doubled in 1966; aerofoil wings introduced in 1968; customer Cosworth DFV engine allowed private teams to win. | Lotus, Tyrrell, Ferrari, McLaren. |
| **1958–1965: Rear-engine revolution** | Cooper proved rear-engine layout superior; Constructors' Championship inaugurated in 1958; 1.5-litre formula (1961–1965). | Cooper, Lotus, BRM, Ferrari. |
| **1950–1957: Front-engine era** | Pre-war style cars, minimal safety rules, very high mechanical attrition and retirement rates. | Alfa Romeo, Ferrari, Maserati, Mercedes. |

Season length grew from 7 races in 1950 to 24 in 2024. Modern drivers face far more reliable cars and stable grids than early-era drivers did, drastically altering base rates for podiums and retirements.

---

## Oddities of Early F1 That Show Up in the Data

Practices from the 1950s and 1960s break several modern assumptions:

* **Shared Drives:** Until 1957, teams could call a car into the pits and swap drivers mid-race. A lead driver whose car broke down could take over a teammate's car. Championship points were divided equally among shared drivers. In the database, this manifests as:
  * One driver having multiple rows for the same `raceId` (one per car driven).
  * Two drivers sharing the same finishing position.
  * *Resolution rule required:* Establish a deterministic rule (e.g., retain the car the driver started in where `grid > 0`, or break ties using best `positionOrder`).
* **The Indianapolis 500 (1950–1960):** Counted toward the World Championship, but virtually no European F1 regulars entered, and Indy drivers rarely contested other rounds. It inflates race counts for American drivers, distorts home-race analysis (Question 2), and has an entirely different grid structure. Excluding these 11 races is a standard and defensible choice.
* **Oversized, Uneven Fields & Non-Qualifiers:** Many privateers entered single races, and fields regularly exceeded grid capacities in the 1980s and 1990s. Non-qualifiers (DNQ/DNPQ) are recorded in `results.csv`, depressing historical podium base rates per row.
* **Team and Driver Identity Drift:** Drivers switched teams mid-season frequently, car numbers were not assigned permanently, and constructors rebranded frequently (e.g., Toleman $\to$ Benetton $\to$ Renault $\to$ Lotus $\to$ Alpine). A "constructor form" feature must track `constructorId` directly while acknowledging rebrands.
* **Low Mechanical Reliability:** Extreme attrition rates in earlier decades mean starting from pole position or the front row converted to a podium far less consistently than in modern racing.