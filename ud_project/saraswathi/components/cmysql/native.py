NATIVE_FUNC_MYSQL_MARIA = """

-- Operators
>	Greater than operator	
>=	Greater than or equal operator	
<	Less than operator	
<>, !=	Not equal operator	
<=	Less than or equal operator	
%, MOD	Modulo operator	
*	Multiplication operator	
+	Addition operator	
-	Minus operator	
-	Change the sign of the argument	
/	Division operator	
:=	Assign a value	
=	Assign a value (as part of a SET statement, or as part of the SET clause in an UPDATE statement)	
=	Equal operator	

-- Functions
ABS()	Return the absolute value	
ADDDATE()	Add time values (intervals) to a date value	
ADDTIME()	Add time	
AND, &&	Logical AND	
ANY_VALUE()	Suppress ONLY_FULL_GROUP_BY value rejection	
ASCII()	Return numeric value of left-most character	
AVG()	Return the average value of the argument	
BETWEEN ... AND ...	Whether a value is within a range of values	
CASE	Case operator	
CAST()	Cast a value as a certain type	
CEIL()	Return the smallest integer value not less than the argument	
CEILING()	Return the smallest integer value not less than the argument			
COALESCE()	Return the first non-NULL argument	
COERCIBILITY()	Return the collation coercibility value of the string argument	
COLLATION()	Return the collation of the string argument		
CONCAT()	Return concatenated string	
CONCAT_WS()	Return concatenate with separator	
CONV()	Convert numbers between different number bases	
CONVERT()	Cast a value as a certain type		
COUNT()	Return a count of the number of rows returned	
COUNT(DISTINCT)	Return the count of a number of different values	
CUME_DIST()	Cumulative distribution value	
CURDATE()	Return the current date	
CURRENT_DATE(), CURRENT_DATE	Synonyms for CURDATE()	
CURRENT_ROLE()	Return the current active roles	
CURRENT_TIME(), CURRENT_TIME	Synonyms for CURTIME()	
CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP	Synonyms for NOW()	
CURRENT_USER(), CURRENT_USER	The authenticated user name and host name	
CURTIME()	Return the current time	
DATE()	Extract the date part of a date or datetime expression	
DATE_ADD()	Add time values (intervals) to a date value	
DATE_FORMAT()	Format date as specified	
DATE_SUB()	Subtract a time value (interval) from a date	
DATEDIFF()	Subtract two dates	
DAY()	Synonym for DAYOFMONTH()	
DAYNAME()	Return the name of the weekday	
DAYOFMONTH()	Return the day of the month (0-31)	
DAYOFWEEK()	Return the weekday index of the argument	
DAYOFYEAR()	Return the day of the year (1-366)	
DEFAULT()	Return the default value for a table column	
DENSE_RANK()	Rank of current row within its partition, without gaps	
DIV	Integer division	
ELT()	Return string at index number	
EXISTS()	Whether the result of a query contains any rows	
EXP()	Raise to the power of	
EXTRACT()	Extract part of a date	
ExtractValue()	Extract a value from an XML string using XPath notation	
FIRST_VALUE()	Value of argument from first row of window frame	
FLOOR()	Return the largest integer value not greater than the argument	
FORMAT()	Return a number formatted to specified number of decimal places	
FOUND_ROWS()	For a SELECT with a LIMIT clause, the number of rows that would be returned were there no LIMIT clause	
FROM_DAYS()	Convert a day number to a date	
FROM_UNIXTIME()	Format Unix timestamp as a date	
GET_FORMAT()	Return a date format string		
GREATEST()	Return the largest argument	
GROUP_CONCAT()	Return a concatenated string	
GROUPING()	Distinguish super-aggregate ROLLUP rows from regular rows	
HOUR()	Extract the hour	
IF()	If/else construct	
IFNULL()	Null if/else construct	
IN()	Whether a value is within a set of values		
INSERT()	Insert substring at specified position up to specified number of characters	
INSTR()	Return the index of the first occurrence of substring	
IS	Test a value against a boolean	
IS NOT	Test a value against a boolean	
IS NOT NULL	NOT NULL value test	
IS NULL	NULL value test		
ISNULL()	Test whether the argument is NULL	
LAG()	Value of argument from row lagging current row within partition	
LAST_DAY	Return the last day of the month for the argument	
LAST_VALUE()	Value of argument from last row of window frame	
LCASE()	Synonym for LOWER()		
LIKE	Simple pattern matching	
LOCALTIME(), LOCALTIME	Synonym for NOW()	
LOCALTIMESTAMP, LOCALTIMESTAMP()	Synonym for NOW()	
MAKE_SET()	Return a set of comma-separated strings that have the corresponding bit in bits set	
MAX()	Return the maximum value	
MIN()	Return the minimum value	
MOD()	Return the remainder	
MONTH()	Return the month from the date passed	
MONTHNAME()	Return the name of the month	
NAME_CONST()	Cause the column to have the given name	
NOT, !	Negates value	
NOT BETWEEN ... AND ...	Whether a value is not within a range of values	
NOT EXISTS()	Whether the result of a query contains no rows	
NOT IN()	Whether a value is not within a set of values	
NOT LIKE	Negation of simple pattern matching	
NOT REGEXP	Negation of REGEXP	
NOW()	Return the current date and time	
NULLIF()	Return NULL if expr1 = expr2	
OCTET_LENGTH()	Synonym for LENGTH()	
OR, ||	Logical OR		
PERCENT_RANK()	Percentage rank value	
PERIOD_ADD()	Add a period to a year-month	
PERIOD_DIFF()	Return the number of months between periods	
POSITION()	Synonym for LOCATE()	
QUARTER()	Return the quarter from a date argument	
RADIANS()	Return argument converted to radians	
RAND()	Return a random floating-point value	
RANK()	Rank of current row within its partition, with gaps	
REGEXP	Whether string matches regular expression	
REGEXP_INSTR()	Starting index of substring matching regular expression	
REGEXP_LIKE()	Whether string matches regular expression	
REGEXP_REPLACE()	Replace substrings matching regular expression	
REGEXP_SUBSTR()	Return substring matching regular expression	
ROUND()	Round the argument	
ROW_COUNT()	The number of rows updated	
ROW_NUMBER()	Number of current row within its partition	
RPAD()	Append string the specified number of times	
RTRIM()	Remove trailing spaces	
SQRT()	Return the square root of the argument		
STD()	Return the population standard deviation	
STR_TO_DATE()	Convert a string to a date	
STRCMP()	Compare two strings	
SUBDATE()	Synonym for DATE_SUB() when invoked with three arguments	
SUBSTR()	Return the substring as specified	
SUBSTRING()	Return the substring as specified	
SUBSTRING_INDEX()	Return a substring from a string before the specified number of occurrences of the delimiter	
SUBTIME()	Subtract times	
SUM()	Return the sum	
TIME()	Extract the time portion of the expression passed	
TIME_FORMAT()	Format as time	
TIMEDIFF()	Subtract time	
TIMESTAMP()	With a single argument, this function returns the date or datetime expression; with two arguments, the sum of the arguments	
TIMESTAMPADD()	Add an interval to a datetime expression	
TIMESTAMPDIFF()	Return the difference of two datetime expressions, using the units specified	
TO_DAYS()	Return the date argument converted to days	
TRUNCATE()	Truncate to specified number of decimal places	
UCASE()	Synonym for UPPER()	
UPPER()	Convert to uppercase	
VALUES()	Define the values to be used during an INSERT	
VAR_POP()	Return the population standard variance	
VAR_SAMP()	Return the sample variance	
WEEK()	Return the week number	
WEEKDAY()	Return the weekday index	
WEEKOFYEAR()	Return the calendar week of the date (1-53)	
YEAR()	Return the year	
"""

NATIVE_FUNC_SQLSERVER = """

-- Operators
>	Greater than operator	
>=	Greater than or equal operator	
<	Less than operator	
<>, !=	Not equal operator	
<=	Less than or equal operator	
%, MODULO	Modulo operator	
*	Multiplication operator	
+	Addition operator	
-	Minus operator	
-	Change the sign of the argument	
/	Division operator	
=	Assign a value (in a SET statement or UPDATE clause)	
=	Equal operator	

-- Functions
ABS()	Return the absolute value	
DATEADD()	Add time values (intervals) to a date value	
DATEADD()	Add time	
AND	Logical AND	
-- SQL Server doesn't have an equivalent to ANY_VALUE()
ASCII()	Return numeric value of left-most character	
AVG()	Return the average value of the argument	
BETWEEN ... AND ...	Whether a value is within a range of values	
CASE	Case operator	
CAST()	Cast a value as a certain type	
CEILING()	Return the smallest integer value not less than the argument	
CEILING()	Return the smallest integer value not less than the argument			
COALESCE()	Return the first non-NULL argument	
COLLATE	Specify collation for comparison	
COLLATIONPROPERTY()	Return the collation of the string argument		
CONCAT()	Return concatenated string	
CONCAT_WS()	-- Not available in SQL Server, use CONCAT() with alternative logic
CONVERT()	Convert numbers between different number bases and types	
CONVERT()	Cast a value as a certain type		
COUNT()	Return a count of the number of rows returned	
COUNT(DISTINCT)	Return the count of a number of different values	
CUME_DIST()	Cumulative distribution value	
GETDATE()	Return the current date and time	
CAST(GETDATE() AS DATE)	Return the current date	
CURRENT_TIMESTAMP	Synonym for GETDATE()	
SUSER_NAME()	The authenticated user name	
CAST(GETDATE() AS TIME)	Return the current time	
CAST(expression AS DATE)	Extract the date part of a date or datetime expression	
DATEADD()	Add time values (intervals) to a date value	
FORMAT()	Format date as specified	
DATEADD()	Add a time value (interval) to a date	
DATEDIFF()	Subtract two dates	
DAY()	Return the day of the month (1-31)	
DATENAME()	Return the name of the weekday	
DAY()	Return the day of the month (1-31)	
DATEPART(weekday, date)	Return the weekday index of the argument	
DATEPART(dayofyear, date)	Return the day of the year (1-366)	
-- SQL Server doesn't have a DEFAULT() function, use DEFAULT constraint instead
DENSE_RANK()	Rank of current row within its partition, without gaps	
/	Integer division	
-- SQL Server doesn't have an ELT() function, use CASE statement instead
EXISTS	Whether the result of a query contains any rows	
EXP()	Raise to the power of	
DATEPART()	Extract part of a date	
-- SQL Server doesn't have ExtractValue(), use XQuery methods instead
FIRST_VALUE()	Value of argument from first row of window frame	
FLOOR()	Return the largest integer value not greater than the argument	
FORMAT()	Return a number formatted to specified number of decimal places	
@@ROWCOUNT	For a SELECT with a TOP clause, the number of rows that would be returned were there no TOP clause	
-- No direct equivalent for FROM_DAYS(), use DATEADD() instead
DATEADD(second, @unixtime, '1970-01-01')	Convert Unix timestamp to a date	
-- SQL Server doesn't have GET_FORMAT(), use FORMAT() instead		
-- Use MAX() for GREATEST() functionality
STRING_AGG()	Return a concatenated string	
GROUPING()	Distinguish super-aggregate ROLLUP rows from regular rows	
DATEPART(hour, date)	Extract the hour	
IIF()	If/else construct	
ISNULL()	Null if/else construct	
IN	Whether a value is within a set of values		
STUFF()	Insert substring at specified position up to specified number of characters	
CHARINDEX()	Return the index of the first occurrence of substring	
IS	Test a value against a boolean	
IS NOT	Test a value against a boolean	
IS NOT NULL	NOT NULL value test	
IS NULL	NULL value test		
ISNULL()	Test whether the argument is NULL	
LAG()	Value of argument from row lagging current row within partition	
EOMONTH()	Return the last day of the month for the argument	
LAST_VALUE()	Value of argument from last row of window frame	
LOWER()	Convert to lowercase		
LIKE	Simple pattern matching	
GETDATE()	Synonym for current date and time	
GETDATE()	Synonym for current date and time	
-- SQL Server doesn't have MAKE_SET(), use alternative logic
MAX()	Return the maximum value	
MIN()	Return the minimum value	
%	Return the remainder	
MONTH()	Return the month from the date passed	
DATENAME(month, date)	Return the name of the month	
-- SQL Server doesn't have NAME_CONST()
NOT	Negates value	
NOT BETWEEN ... AND ...	Whether a value is not within a range of values	
NOT EXISTS	Whether the result of a query contains no rows	
NOT IN	Whether a value is not within a set of values	
NOT LIKE	Negation of simple pattern matching	
NOT LIKE	Negation of pattern matching	
GETDATE()	Return the current date and time	
NULLIF()	Return NULL if expr1 = expr2	
DATALENGTH()	Return the number of bytes	
OR	Logical OR		
PERCENT_RANK()	Percentage rank value	
-- No direct equivalent for PERIOD_ADD(), use DATEADD() instead
-- No direct equivalent for PERIOD_DIFF(), use DATEDIFF() instead
CHARINDEX()	Return the position of a substring	
DATEPART(quarter, date)	Return the quarter from a date argument	
RADIANS()	Return argument converted to radians	
RAND()	Return a random floating-point value	
RANK()	Rank of current row within its partition, with gaps	
LIKE	Pattern matching (use with '%' and '_')	
PATINDEX()	Starting index of substring matching pattern	
LIKE	Pattern matching	
REPLACE()	Replace substrings	
SUBSTRING()	Return substring matching pattern	
ROUND()	Round the argument	
@@ROWCOUNT	The number of rows affected	
ROW_NUMBER()	Number of current row within its partition	
RIGHT()	Append string the specified number of times	
RTRIM()	Remove trailing spaces	
SQRT()	Return the square root of the argument		
STDEV()	Return the population standard deviation	
CONVERT()	Convert a string to a date	
-- SQL Server doesn't have STRCMP(), use CASE statement for string comparison
DATEADD()	Add time values (intervals) to a date value	
SUBSTRING()	Return the substring as specified	
SUBSTRING()	Return the substring as specified	
-- SQL Server doesn't have SUBSTRING_INDEX(), use alternative logic
DATEADD()	Add times	
SUM()	Return the sum	
CAST(expression AS TIME)	Extract the time portion of the expression passed	
FORMAT()	Format as time	
DATEDIFF()	Subtract time	
-- SQL Server TIMESTAMP is different, use DATETIME or DATETIME2	
DATEADD()	Add an interval to a datetime expression	
DATEDIFF()	Return the difference of two datetime expressions, using the units specified	
-- No direct equivalent for TO_DAYS(), use alternative date calculations
ROUND()	Round to specified number of decimal places	
UPPER()	Convert to uppercase	
UPPER()	Convert to uppercase	
-- Use INSERT ... SELECT for similar functionality to VALUES()	
VAR()	Return the population standard variance	
VAR()	Return the sample variance	
DATEPART(week, date)	Return the week number	
DATEPART(weekday, date)	Return the weekday index	
DATEPART(week, date)	Return the calendar week of the date (1-53)	
YEAR()	Return the year
"""

NATIVE_FUNC_POSTGRESQL = """
-- Operators
>	Greater than operator
>=	Greater than or equal operator
<	Less than operator
<>, !=	Not equal operator
<=	Less than or equal operator
%	Modulo operator
*	Multiplication operator
+	Addition operator
-	Minus operator
-	Change the sign of the argument
/	Division operator
:=	Assignment operator (Used in PL/pgSQL for variable assignment)
=	Equal operator

-- Functions
ABS()	        Return the absolute value
AGE()	        Subtract two dates (similar to DATEDIFF())
AVG()	        Return the average value of the argument
BETWEEN ... AND ...	Whether a value is within a range of values
CASE	        Case operator
CAST()	        Cast a value as a certain type
CEIL()	        Return the smallest integer value not less than the argument
CEILING()	Return the smallest integer value not less than the argument
COALESCE()	Return the first non-NULL argument
COLLATION()	Return the collation of the string argument
CONCAT()	Return concatenated string
CONCAT_WS()	Return concatenated string with separator
CONVERT()	Convert a value to a certain type
COUNT()	        Return a count of the number of rows returned
COUNT(DISTINCT)	Return the count of different values
CURRENT_DATE()	Return the current date
CURRENT_TIME()	Return the current time
CURRENT_TIMESTAMP()	Return the current date and time
CURRENT_USER()	Return the current user
DATE()	        Extract the date part of a timestamp
DATE_PART()	Extract subfields such as year or hour from date/time values
DATE_TRUNC()	Truncate date/time to a specified precision
DATEADD()	Use + interval (e.g., '2024-08-22' + interval '1 day')
DATE_SUB()	Use - interval (e.g., '2024-08-22' - interval '1 day')
DAY()	        Extract the day of the month (equivalent to EXTRACT(DAY FROM ...))
DAYOFMONTH()	Extract the day of the month (equivalent to EXTRACT(DAY FROM ...))
DAYOFWEEK()	Extract the weekday index (Sunday = 0, equivalent to EXTRACT(DOW FROM ...))
DAYOFYEAR()	Extract the day of the year (equivalent to EXTRACT(DOY FROM ...))
DIV()	        Integer division operator (/)
EXISTS()	Whether the result of a query contains any rows
EXP()	        Raise to the power of
EXTRACT()	Extract subfields such as year, month, or hour from date/time values
FIRST_VALUE()	Value of argument from first row of window frame
FLOOR()	        Return the largest integer value not greater than the argument
FORMAT()	Return a formatted string (use the `to_char()` function in PostgreSQL)
GREATEST()	Return the largest argument
GROUP_CONCAT()	String aggregation (use `string_agg()` in PostgreSQL)
HOUR()	        Extract the hour (equivalent to EXTRACT(HOUR FROM ...))
IF()	        Use CASE or COALESCE in PostgreSQL
IFNULL()	Null if/else construct (use COALESCE() in PostgreSQL)
IN()	        Whether a value is within a set of values
INSERT()	Insert a substring into a string (use the `overlay()` function in PostgreSQL)
INSTR()		Position of substring in string (use `position()` in PostgreSQL)
IS NOT NULL	NOT NULL value test
IS NULL	NULL value test
ISNULL()	Test whether the argument is NULL
LAG()	        Value of argument from row lagging current row within partition
LAST_DAY()	Return the last day of the month for the argument (use `date_trunc('month', date)` + interval '1 month - 1 day')
LAST_VALUE()	Value of argument from last row of window frame
LCASE()	        Convert to lowercase (use LOWER() in PostgreSQL)
LEAD()	        Value of argument from row leading current row within partition
LEAST()	        Return the smallest argument
LEFT()	        Extract the left part of a string
LEN()	        Return the length of a string (use `length()` in PostgreSQL)
LIKE	        Simple pattern matching
LOCALTIME()	Return the current time
LOCALTIMESTAMP	Return the current date and time
LPAD()	        Pad the left side of a string
LTRIM()	        Remove leading spaces
MAX()	        Return the maximum value
MIN()	        Return the minimum value
MOD()	        Return the remainder
MONTH()	        Extract the month (equivalent to EXTRACT(MONTH FROM ...))
MONTHNAME()	Return the name of the month (use `to_char()` with 'Month' format)
NOT, !	        Negation operator
NOT BETWEEN ... AND ...	Whether a value is not within a range of values
NOT EXISTS()	Whether the result of a query contains no rows
NOT IN()	Whether a value is not within a set of values
NOT LIKE	Negation of simple pattern matching
NOW()	        Return the current date and time
NULLIF()	Return NULL if expr1 = expr2
OCTET_LENGTH()	Return the length of a string in bytes (similar to `length()` in PostgreSQL)
OR, ||	        Logical OR
POSITION()	Synonym for LOCATE()
QUARTER()	Return the quarter from a date argument (use `EXTRACT(QUARTER FROM ...)`)
RADIANS()	Return argument converted to radians
RAND()	        Return a random floating-point value (use `random()` in PostgreSQL)
REGEXP	        Whether string matches regular expression (use `~` in PostgreSQL)
REGEXP_REPLACE()	Replace substrings matching regular expression
REGEXP_SUBSTR()	Return substring matching regular expression
ROUND()	Round the argument
ROW_NUMBER()	Number of current row within its partition
RPAD()	Pad the right side of a string
RTRIM()	Remove trailing spaces
SQRT()	Return the square root of the argument
STRING_AGG()	String aggregation (similar to `GROUP_CONCAT()` in MySQL)
STRPOS()	Return the position of a substring in a string
SUBSTR()	Return a substring from a string
SUBSTRING()	Return a substring from a string
SUM()	Return the sum of values
TIME()	Extract the time portion of the expression passed (use `EXTRACT(HOUR, MINUTE, SECOND FROM ...)`)
TIMEDIFF()	Subtract two time values (use `-` between two time values)
TIMESTAMP()	Return the current date and time
TO_CHAR()	Format date/time values (equivalent to `DATE_FORMAT()` in MySQL)
TO_DATE()	Convert a string to a date
TO_NUMBER()	Convert a string to a numeric value
TRIM()	Remove leading and trailing spaces
TRUNC()	Truncate to a specified number of decimal places
UPPER()	Convert to uppercase
VAR_POP()	Return the population standard variance
VAR_SAMP()	Return the sample variance
WEEK()	Return the week number of a date (use `EXTRACT(WEEK FROM ...)`)
WEEKDAY()	Return the weekday index (use `EXTRACT(DOW FROM ...)`)
YEAR()	Extract the year (equivalent to `EXTRACT(YEAR FROM ...)`)
"""

NATIVE_FUNC_ORACLE = """

-- Operators
>	Greater than operator	
>=	Greater than or equal operator	
<	Less than operator	
<>, !=	Not equal operator	
<=	Less than or equal operator	
MOD	Modulo operator	
*	Multiplication operator	
+	Addition operator	
-	Minus operator	
-	Change the sign of the argument	
/	Division operator	
:=	Assignment operator (in PL/SQL)	
=	Assign a value (in UPDATE statements)	
=	Equal operator	

-- Functions
ABS()	Return the absolute value	
ADD_MONTHS()	Add months to a date	
-- No direct equivalent for ADDTIME(), use DATE arithmetic
AND	Logical AND	
-- No direct equivalent for ANY_VALUE()
ASCII()	Return numeric value of left-most character	
AVG()	Return the average value of the argument	
BETWEEN ... AND ...	Whether a value is within a range of values	
CASE	Case operator	
CAST()	Cast a value as a certain type	
CEIL()	Return the smallest integer value not less than the argument	
CEILING()	Return the smallest integer value not less than the argument			
COALESCE()	Return the first non-NULL argument	
-- No direct equivalent for COERCIBILITY()
-- Use NLS_SORT for collation-related operations
CONCAT() or ||	Return concatenated string	
-- No direct equivalent for CONCAT_WS(), use LISTAGG() or custom function
TO_NUMBER()	Convert numbers between different number bases	
TO_CHAR(), TO_DATE(), TO_NUMBER()	Cast a value as a certain type		
COUNT()	Return a count of the number of rows returned	
COUNT(DISTINCT)	Return the count of a number of different values	
CUME_DIST()	Cumulative distribution value	
TRUNC(SYSDATE)	Return the current date	
TRUNC(SYSDATE)	Return the current date	
-- No direct equivalent for CURRENT_ROLE(), use SYS_CONTEXT()
CURRENT_TIMESTAMP	Return the current timestamp	
CURRENT_TIMESTAMP	Return the current timestamp	
USER	The authenticated user name	
TO_CHAR(SYSTIMESTAMP, 'HH24:MI:SS')	Return the current time	
TRUNC()	Extract the date part of a date or datetime expression	
ADD_MONTHS(), INTERVAL	Add time values (intervals) to a date value	
TO_CHAR()	Format date as specified	
ADD_MONTHS(), INTERVAL	Subtract a time value (interval) from a date	
-- Use DATE arithmetic for DATEDIFF functionality
EXTRACT(DAY FROM date)	Return the day of the month (1-31)	
TO_CHAR(date, 'Day')	Return the name of the weekday	
EXTRACT(DAY FROM date)	Return the day of the month (1-31)	
TO_CHAR(date, 'D')	Return the weekday index of the argument	
TO_CHAR(date, 'DDD')	Return the day of the year (1-366)	
-- No direct equivalent for DEFAULT(), use NVL() or COALESCE()
DENSE_RANK()	Rank of current row within its partition, without gaps	
-- Use TRUNC() for integer division
-- No direct equivalent for ELT(), use CASE statement
EXISTS	Whether the result of a query contains any rows	
EXP()	Raise to the power of	
EXTRACT()	Extract part of a date	
EXTRACTVALUE()	Extract a value from an XML string using XPath notation	
FIRST_VALUE()	Value of argument from first row of window frame	
FLOOR()	Return the largest integer value not greater than the argument	
TO_CHAR()	Format number or date as specified	
-- No direct equivalent for FOUND_ROWS(), use ROWNUM or row limiting clause
-- No direct equivalent for FROM_DAYS(), use DATE arithmetic
-- Use TO_DATE() and DATE arithmetic for FROM_UNIXTIME functionality
-- Use TO_CHAR() for GET_FORMAT functionality		
GREATEST()	Return the largest argument	
LISTAGG()	Return a concatenated string	
GROUPING()	Distinguish super-aggregate ROLLUP rows from regular rows	
EXTRACT(HOUR FROM timestamp)	Extract the hour	
-- Use CASE for IF functionality
NVL()	Null if/else construct	
IN	Whether a value is within a set of values		
-- Use SUBSTR() and INSTR() to replicate INSERT() functionality
INSTR()	Return the index of the first occurrence of substring	
IS	Test a value against a boolean	
IS NOT	Test a value against a boolean	
IS NOT NULL	NOT NULL value test	
IS NULL	NULL value test		
-- Use NVL() or CASE for ISNULL() functionality
LAG()	Value of argument from row lagging current row within partition	
LAST_DAY()	Return the last day of the month for the argument	
LAST_VALUE()	Value of argument from last row of window frame	
LOWER()	Convert to lowercase		
LIKE	Simple pattern matching	
CURRENT_TIMESTAMP	Synonym for current timestamp	
CURRENT_TIMESTAMP	Synonym for current timestamp	
-- No direct equivalent for MAKE_SET(), use custom function
MAX()	Return the maximum value	
MIN()	Return the minimum value	
MOD()	Return the remainder	
EXTRACT(MONTH FROM date)	Return the month from the date passed	
TO_CHAR(date, 'Month')	Return the name of the month	
-- No direct equivalent for NAME_CONST()
NOT	Negates value	
NOT BETWEEN ... AND ...	Whether a value is not within a range of values	
NOT EXISTS	Whether the result of a query contains no rows	
NOT IN	Whether a value is not within a set of values	
NOT LIKE	Negation of simple pattern matching	
NOT REGEXP_LIKE	Negation of REGEXP_LIKE	
CURRENT_TIMESTAMP	Return the current date and time	
NULLIF()	Return NULL if expr1 = expr2	
LENGTH()	Return the length of a string in bytes	
OR	Logical OR		
PERCENT_RANK()	Percentage rank value	
ADD_MONTHS()	Add months to a date	
MONTHS_BETWEEN()	Return the number of months between dates	
INSTR()	Return the position of a substring	
TO_CHAR(date, 'Q')	Return the quarter from a date argument	
-- Use PI()/180 * n to convert to radians
DBMS_RANDOM.VALUE	Return a random floating-point value	
RANK()	Rank of current row within its partition, with gaps	
REGEXP_LIKE	Whether string matches regular expression	
REGEXP_INSTR()	Starting index of substring matching regular expression	
REGEXP_LIKE()	Whether string matches regular expression	
REGEXP_REPLACE()	Replace substrings matching regular expression	
REGEXP_SUBSTR()	Return substring matching regular expression	
ROUND()	Round the argument	
SQL%ROWCOUNT	The number of rows affected	
ROW_NUMBER()	Number of current row within its partition	
RPAD()	Append string the specified number of times	
RTRIM()	Remove trailing spaces	
SQRT()	Return the square root of the argument		
STDDEV()	Return the population standard deviation	
TO_DATE()	Convert a string to a date	
-- Use CASE or DECODE() for string comparison
-- Use ADD_MONTHS() or INTERVAL for date subtraction
SUBSTR()	Return the substring as specified	
SUBSTR()	Return the substring as specified	
-- No direct equivalent for SUBSTRING_INDEX(), use custom function
-- Use DATE arithmetic for SUBTIME functionality
SUM()	Return the sum	
TO_CHAR(date, 'HH24:MI:SS')	Extract the time portion of the expression passed	
TO_CHAR()	Format as time	
-- Use DATE arithmetic for TIMEDIFF functionality
-- Oracle TIMESTAMP is similar to MySQL TIMESTAMP	
-- Use INTERVAL or DATE arithmetic to add intervals to dates
-- Use NUMTODSINTERVAL() to find difference between dates
-- No direct equivalent for TO_DAYS(), use DATE arithmetic
TRUNC()	Truncate to specified number of decimal places	
UPPER()	Convert to uppercase	
UPPER()	Convert to uppercase	
-- Use INSERT ... SELECT for similar functionality to VALUES()	
VAR_POP()	Return the population variance	
VAR_SAMP()	Return the sample variance	
TO_CHAR(date, 'IW')	Return the week number	
TO_CHAR(date, 'D')	Return the weekday index	
TO_CHAR(date, 'IW')	Return the calendar week of the date (1-53)	
EXTRACT(YEAR FROM date)	Return the year
"""
