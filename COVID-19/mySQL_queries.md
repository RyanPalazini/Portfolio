<h3>Data acquired from:</h3>
<p>https://ourworldindata.org/covid-deaths<br>
https://github.com/owid/covid-19-data/tree/master/public/data</p>

The raw data is contained in a single table, but was split into tables <i>deaths</i> and <i>vaccinations</i> for the purpose of these queries. This increased the opportunity to demonstrate joins and them more readable when a self-join would have been necessary regardless.


<br><h4>Total Cases and Total Deaths in United States</h4>

```mySQL
SELECT
	location,
	date,
	total_cases,
	total_deaths,
	(total_deaths / total_cases) * 100 AS OverallDeathRate
FROM Deaths
WHERE location = "United States"
ORDER BY date DESC;
```


<br><h4>Overall death rate to date (May 24, 2022)</h4>

```mySQL
SELECT
    location,
    date,
    total_cases,
    total_deaths,
  	ROUND((total_deaths / total_cases) * 100,3) AS Death_Rate
FROM Deaths
WHERE date = '2022-05-24'
ORDER BY Death_Rate DESC;
```


<br><h4>Current total deaths by country</h4>

```mySQL
SELECT location, MAX(total_deaths) as 'Total_Deaths'
FROM Deaths
WHERE continent <> ''
GROUP BY location
ORDER BY Total_Deaths DESC;
```


<br><h4>Daily Hospitalization info including estimate of hospital capcity (percentage)</h4>

```mySQL
SELECT 
	v.location,
	v.date,
	d.new_deaths/d.new_cases AS DateDeathRate,
	v.hosp_patients,
	v.icu_patients,
	(v.weekly_icu_admissions / v.weekly_hosp_admissions) AS WeeklyPercentICU,
	(v.hosp_patients / ((v.population/1000) * v.hospital_beds_per_thousand)) AS HospCapacityEstimate
FROM Vaccinations v
LEFT JOIN Deaths d 
ON v.location = d.location AND v.date = d.date
ORDER BY HospCapacityEstimate DESC;
```


<br><h4>Using subquery to gather global info</h4>

```mySQL
SELECT
	date,
	Global_New_Cases,
	Global_New_Deaths,
 	ROUND((Global_New_Deaths / Global_New_Cases)*100, 3) AS 'Date_Death_Rate',
 	Global_Total_Cases,
 	Global_Total_Deaths,
 	ROUND((Global_Total_Deaths / Global_Total_Cases) * 100, 3) AS 'Global_Overall_Death_Rate'
FROM 
	(SELECT 
		date,
		sum(new_cases) AS 'Global_New_Cases',
		sum(new_deaths) AS 'Global_New_Deaths',
		sum(total_cases) AS 'Global_Total_Cases',
		sum(total_deaths) AS 'Global_Total_Deaths'
	FROM Deaths
	GROUP BY date) x
ORDER BY date DESC;
```




<br><h4>Using CTE for percentage of population vaccinated, using window function for rolling vaccination count</h4>

```mySQL
With PopVac (continent, location, date, population, new_vaccinations, RollingVaccinations) AS
(
SELECT 
	d.continent, 
	d.location, 
	d.date, 
	d.population, 
	v.new_vaccinations,
	sum(v.new_vaccinations) OVER (PARTITION BY d.location ORDER BY d.location, d.date) as RollingVaccinations 
FROM Deaths d
LEFT JOIN Vaccination v
ON d.location = v.location and d.date = v.date
)
SELECT *, ROUND(RollingVaccinations/population * 100, 3) as CountryPercentVaccinated
FROM PopVac
ORDER BY location, date DESC;
```



<br><h4>Using temp table for percentage of population vaccinated, using window function for rolling vaccination count (same result as previous query)</h4>

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


<br><h4>Using CTE and OVER clause to estimate the rate at which COVID is spreading.</h4>

According to CDC update Januart 14, 2022: 
> There's "an average period of infectiousness and risk of transmission between 2-3 days before and 8 days after symptom onset."
(https://www.cdc.gov/coronavirus/2019-ncov/hcp/duration-isolation.html)

It will be assumed that the new cases on any given day were infected by the new cases of the previous 10 days--those who were still infectious.
Truly calculating the spread requires much more complicated methods, such as a Susceptible-Exposed-Infected-Removed (SEIR) Model. In other words,
this is not an actual metric of spread, but is merely for exercise.

```mySQL
WITH Spread (location, date, new_cases, RollingCases) AS
(
SELECT 
	location,
	date,
	new_cases,
	sum(new_cases) OVER (PARTITION BY location ORDER BY date ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) as RollingCases 
FROM Deaths
)
SELECT *, ROUND(New_Cases/RollingCases * 100, 3) as DailySpreadPercentage
FROM Spread
ORDER BY location, date DESC;
```



<br><h4>Death Rate, percent vaccinated, etc. by country during the past year</h4>
Many locations do not provide fully vaccinated data or total_boosters, so that data is particularly incomplete

```mySQL
WITH YearData (location, date, gdp_per_capita, population_density, YearCases, YearDeaths) AS
(
SELECT 
	location,
	date,
	gdp_per_capita,
	population_density,
	SUM(new_cases) OVER (PARTITION BY location ORDER BY date) AS YearCases,
	SUM(new_deaths) OVER (PARTITION BY location ORDER BY date) AS YearDeaths
FROM Deaths d
WHERE 
	new_cases IS NOT NULL AND
	new_deaths IS NOT NULL AND
	continent <> '' AND
	date > DATE_ADD('2022-05-24', INTERVAL -1 YEAR)
)
SELECT
	y.location,
	y.gdp_per_capita,
	y.YearCases,
	y.YearDeaths,
	y.population_density,
	ROUND(y.YearDeaths/y.YearCases * 100, 3) as YearDeathRate,
	ROUND(v.people_fully_vaccinated/v.population * 100, 3) as PercentFullVax, 
	ROUND(v.total_boosters/v.people_fully_vaccinated, 3) as BoosterPerFullVax 
FROM YearData y
LEFT JOIN vaccinations v
ON y.location=v.location AND y.date = v.date
WHERE
	y.date = '2022-05-24'
ORDER BY gdp_per_capita DESC;
```


<br><h4>Create view for future visualization</h4>
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
