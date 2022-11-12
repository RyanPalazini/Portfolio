<h3>Data:</h3>
<p>https://ourworldindata.org/covid-deaths<br>
https://github.com/owid/covid-19-data/tree/master/public/data</p>

<p>The raw data is contained in a single table, but was split into tables <i>deaths</i> and <i>vaccinations</i> for the purpose of these queries. This increased the opportunity to demonstrate joins and made joins more readable when a self-join would have been necessary regardless. These tables are included in the repository folder <i>COVID-19</i>.</p>

<h3>Queries:</h3>
<h4>1. Total Cases and Total Deaths in United States</h4>

```mySQL
SELECT
	location,
	date,
	total_cases,
	total_deaths,
	(total_deaths / total_cases) * 100 AS overall_death_percentage
FROM Deaths
WHERE location = "United States"
ORDER BY date DESC;
```

<br><h4>2. Current total deaths by country</h4>
```mySQL
SELECT location, MAX(total_deaths) as total_deaths
FROM deaths
WHERE continent <> ''
GROUP BY location
ORDER BY total_deaths DESC;
```

<br><h4>3. Overall death rate by location according to most recent available data</h4>
Incomplete North Korea data result in death_rate = 6, hence the HAVING clause
```mySQL
SELECT 
	continent, 
	location,
	MAX(date),
	MAX(total_deaths) as total_deaths ,
	MAX(total_cases) as total_cases,
	ROUND(MAX(total_deaths)/MAX(total_cases), 5) as death_rate
FROM Deaths
WHERE total_cases IS NOT NULL AND total_deaths IS NOT NULL
GROUP BY continent, location
HAVING death_Rate <= 1
ORDER BY death_Rate DESC;
```

<br><h4>4. Daily Hospitalization info including estimate of hospital capcity (percentage)</h4>
Recognize that the hospital capacity estimate is only for beds occupied by COVID patient
```mySQL
SELECT 
	v.location,
	v.date,
	d.new_deaths/d.new_cases AS date_death_rate,
	v.hosp_patients,
	v.icu_patients,
	(v.weekly_icu_admissions / v.weekly_hosp_admissions) AS weekly_percent_icu,
	(v.hosp_patients / ((d.population/1000) * v.hospital_beds_per_thousand)) AS hospital_capacity_est
FROM Vaccinations v
LEFT JOIN Deaths d 
ON v.location = d.location AND v.date = d.date
ORDER BY hospital_capacity_est DESC;
```

<br><h4>5. Global Info</h4>

```mySQL
SELECT
	date,
	global_new_cases,
	global_new_deaths,
 	ROUND((global_new_deaths / global_new_cases)*100, 3) AS date_death_rate,
 	global_total_cases,
 	global_total_deaths,
 	ROUND((global_total_deaths / global_total_cases) * 100, 3) AS global_death_rate
FROM 
	(SELECT 
		date,
		sum(new_cases) AS global_new_cases,
		sum(new_deaths) AS global_new_deaths,
		sum(total_cases) AS global_total_cases,
		sum(total_deaths) AS global_Total_deaths
	FROM Deaths
	WHERE continent <> ''
	GROUP BY date) x
ORDER BY date DESC;
```

<br><h4>6. Using CTE for percentage of population vaccinated</h4>

```mySQL
With PopVac AS
(
SELECT 
	d.continent, 
	d.location, 
	d.date, 
	d.population, 
	v.new_vaccinations,
	sum(v.new_vaccinations) OVER (PARTITION BY d.location ORDER BY d.location, d.date) as rolling_vaccinations 
FROM Deaths d
LEFT JOIN Vaccinations v
ON d.location = v.location and d.date = v.date
)
SELECT *, ROUND(rolling_vaccinations /population * 100, 3) as percent_vaccinated
FROM PopVac
ORDER BY location, date DESC;
```

<br><h4>7. Using temp table for percentage of population vaccinated (same as previous query but with temp table)</h4>

```mySQL
CREATE TEMPORARY TABLE IF NOT EXISTS PercentVaccinated
SELECT 
	d.continent, 
	d.location, 
	d.date, 
	d.population, 
	v.new_vaccinations,
	sum(v.new_vaccinations) OVER (PARTITION BY d.location ORDER BY d.location, d.date) as RollingVaccinations 
FROM Deaths d
LEFT JOIN Vaccinations v
ON d.location = v.location and d.date = v.date;

SELECT *, ROUND(RollingVaccinations/population * 100, 3) as CountryPercentVaccinated
FROM PercentVaccinated
ORDER BY location, date DESC;

DROP TEMPORARY TABLE PercentVaccinated;
```

<br><h4>8. Estimate the rate at which COVID is spreading</h4>
 
> There's "an average period of infectiousness and risk of transmission between 2-3 days before and 8 days after symptom onset."
(https://www.cdc.gov/coronavirus/2019-ncov/hcp/duration-isolation.html)

It will be assumed that the new cases on any given day were infected by the new cases of the previous 10 days--those who were still infectious.
Truly calculating the spread requires much more complicated methods, such as a Susceptible-Exposed-Infected-Removed (SEIR) Model. In other words,
this is not an actual metric of spread, but is merely for exercise.

```mySQL
WITH Spread AS
(
SELECT 
	location,
	date,
	new_cases,
	sum(new_cases) OVER (PARTITION BY location ORDER BY date ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS rolling_cases
FROM Deaths
)
SELECT *, ROUND(New_Cases/rolling_cases * 100, 3) as daily_spread_percentage
FROM Spread
ORDER BY location, date DESC;
```

<br><h4>9. Death Rate, percent vaccinated, etc. by country during the past year</h4>
Many locations do not provide fully vaccinated data or total_boosters, so that data is particularly incomplete

```mySQL
WITH YearData AS
(
SELECT 
	location,
	date,
	SUM(new_cases) OVER (PARTITION BY location ORDER BY date) AS year_cases,
	SUM(new_deaths) OVER (PARTITION BY location ORDER BY date) AS year_deaths,
	population
FROM Deaths
WHERE new_cases IS NOT NULL
	AND new_deaths IS NOT NULL
	AND continent <> ''
	AND date > DATE_ADD(CURDATE() , INTERVAL -1 YEAR)
)
SELECT
	y.location,
	y.date,
	y.year_cases,
	y.year_deaths,
	ROUND(y.year_deaths/y.year_cases * 100, 3) as year_death_percentage,
	ROUND(v.people_fully_vaccinated/y.population * 100, 3) as percent_full_vax, 
	ROUND(v.total_boosters/v.people_fully_vaccinated, 3) as booster_per_full_vax,
	v.population_density,
	v.gdp_per_capita
FROM YearData y
LEFT JOIN vaccinations v
	ON y.location = v.location
	AND y.date = v.date
WHERE y.date = CURDATE()
ORDER BY gdp_per_capita DESC;
```
<br><h4>10. Boosters in last 90 days by location:</h4>
 According to the CDC (https://www.cdc.gov/coronavirus/2019-ncov/vaccines/stay-up-to-date.html#novavax-18-and-older),
 an individual can be boosted when 2 months or more have passed since their most recent primary dose or booster.
 For individuals who recently ahd COVID-19, they may consider delaying their next primary dose or booster by 3 months
 from when symptoms started/they tested positive. Most countries do not have up-to-date total_boosters for each date and missing data is stored as an empty string. The following linearly interpolates missing values of total_boosters,
 calculates daily new boosters, and calculates the 90 day rolling sum of new boosters.
 ```mySQL
 -- First, replace empty strings with NULL and change data type
UPDATE Vaccinations
SET total_boosters = NULLIF(total_boosters, '');

ALTER TABLE Vaccinations 
MODIFY COLUMN total_boosters BIGINT;

-- cte Linearly interpolates total_boosters
WITH cte AS
(
SELECT
    location,
    date, 
    CASE
        WHEN ISNULL(total_boosters1) THEN 0
        ELSE ROUND(total_boosters1 + (total_boosters2 - total_boosters1) * (rn - 1) / cnt) 
    END AS total_boosters
FROM
    (
    SELECT
        v.*, 
        min(total_boosters) OVER(PARTITION BY location,grp1) AS total_boosters1,
        min(total_boosters) OVER(PARTITION BY location,grp2) AS total_boosters2,
        count(*) OVER(PARTITION BY location,grp1) AS cnt,
        ROW_NUMBER() OVER(PARTITION BY location, grp1 ORDER BY date) AS rn
    FROM
        (
        SELECT
            location,
            date,
            total_boosters,
            count(total_boosters) OVER(PARTITION BY location ORDER BY date) AS grp1,
            count(total_boosters) OVER(PARTITION BY location ORDER BY date DESC) AS grp2
        FROM vaccinations v
        ) v
    ) v
)
-- Now calculate new_boosters and boosters_90roll
SELECT
    *,
    SUM(boosters_new) OVER(PARTITION BY location 
        ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) AS boosters_90roll
FROM
    (
    SELECT
        location,
        date,
        total_boosters,
        total_boosters - lag_total_boosters AS boosters_new
    FROM
        (
        SELECT
            c.*, 
            LAG(total_boosters) OVER(PARTITION BY location ORDER BY date) AS lag_total_boosters
        FROM cte c
        ) c
    ) c;
 ```
 
<br><h4>11. Create view for future visualization</h4>
```mySQL
CREATE VIEW PercentVaccinated AS
SELECT 
	d.continent, 
	d.location, 
	d.date, 
	d.population, 
	v.new_vaccinations,
	sum(v.new_vaccinations) OVER (PARTITION BY d.location ORDER BY d.location, d.date) as RollingVaccinations 
FROM Deaths d
LEFT JOIN Vaccinations v
ON d.location = v.location and d.date = v.date;
```
