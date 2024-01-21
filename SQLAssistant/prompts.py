# Modified from Langchain's _mysql_prompt
# Originally "at most {top_k} results" allowed llm to incorrectly lower the limit from top_k.
mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for {top_k} results using the LIMIT {top_k} clause as per MySQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURDATE() function to get the current date, if the question involves "today".

Use the following format:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here

"""

# From Langchain
prompt_suffix = """Only use the following tables:
{table_info}

Question: {input}"""

few_shots = [
    {
        'Question': "What is total amount rung up by each staff member in August of 2005?",
        'SQLQuery': "SELECT s.first_name, s.last_name, SUM(p.amount) FROM staff s INNER JOIN payment p ON (s.staff_id = p.staff_id) WHERE MONTH(p.payment_date) = 08 AND YEAR(p.payment_date) = 2005 GROUP BY s.staff_id ORDER BY SUM(`p`.`amount`);",
        'SQLResult': "[('Jon', 'Stephens', Decimal('12216.49')), ('Mike', 'Hillyer', Decimal('11853.65'))]",
        'Answer': "Jon Stephens and Mike Hillyer are the top earners in August 2005, with Jon earning 12216.49 and Mike earning 11853.65."
    },
    {
        'Question': "List each film and the number of actors who are listed for that film.",
        'SQLQuery': "SELECT f.title, COUNT(a.actor_id) AS 'Number of Actors' FROM film f INNER join film_actor a ON (f.film_id = a.film_id) GROUP BY f.title ORDER BY 'Number of Actors';",
        'SQLResult': "[('LAMBS CINCINATTI', 15), ('CRAZY HOME', 13), ('DRACULA CRYSTAL', 13), ('CHITTY LOCK', 13), ('BOONDOCK BALLROOM', 13)]",
        'Answer': "LAMBS CINCINATTI has the most actors with 15 actors, followed by CRAZY HOME, DRACULA CRYSTAL, CHITTY LOCK, and BOONDOCK BALLROOM with 13 actors each."
    },
    {
        'Question': "Display the titles of movies starting with the letters `K` and `Q` whose language is English.",
        'SQLQuery': "SELECT title FROM film WHERE title LIKE 'K%' OR title LIKE 'Q%' AND language_id IN (SELECT language_id FROM language WHERE name = 'English');",
        'SQLResult': "[('KANE EXORCIST',), ('KARATE MOON',), ('KENTUCKIAN GIANT',), ('KICK SAVANNAH',), ('KILL BROTHERHOOD',)]",
        'Answer': "KANE EXORCIST, KARATE MOON, KENTUCKIAN GIANT, KICK SAVANNAH, and KILL BROTHERHOOD are some of the English language films that start with the letters K or Q."
    },
    {
        'Question': "Which movie is rented the most for each category?",
        'SQLQuery': "WITH CTE AS (SELECT c.name AS 'Category', f.title AS 'Film_Title', COUNT(r.rental_id) AS 'Times_Rented', DENSE_RANK() OVER (PARTITION BY c.category_id ORDER BY COUNT(r.rental_id) DESC) AS dr FROM film_category fc JOIN category c ON (fc.category_id = c.category_id) JOIN film f ON (fc.film_id = f.film_id) LEFT JOIN inventory i ON (f.film_id = i.film_id) LEFT JOIN rental r ON (i.inventory_id = r.inventory_id) GROUP BY c.name, f.title) SELECT Category, Film_Title, Times_Rented FROM CTE WHERE dr = 1 ORDER BY Times_Rented DESC, Category DESC;",
        'SQLResult': "[('Travel', 'BUCKET BROTHERHOOD', 34), ('Foreign', 'ROCKETEER MOTHER', 33), ('New', 'RIDGEMONT SUBMARINE', 32), ('Music', 'SCALAWAG DUCK', 32), ('Games', 'GRIT CLOCKWORK', 32)]",
        'Answer': "The most rented film in th Travel category is BUCKET BROTHERHOOD with 34 rentals. The most rented film in th Foreign category is ROCKETEER MOTHER with 33 rentals. The most rented film in th New category is RIDGEMONT SUBMARINE with 32 rentals. The most rented film in the Music category is SCALAWAG DUCK with 32 rentals. The most rented film in th Games category is GRIT CLOCKWORK with 32 rentals."    
    }
]