# Covid-19 Centralised Dashboard Project

#### Written and designed to the ECM1400 project specification

##### Developed in python 3.9 | (README Is In Markdown)

This project is designed to gather both live covid-data updates and news 
articles and contain all the information in one, manageable place.
The user has the ability to schedule updates for either covid-data or news
independently, or simultaneously as well as have updates able to repeat, if so
chosen. Also provided is the ability to configure and tailor the dashboard to
a users preferences.

## How To Use

### - Required Modules

A number of extra modules are required to be installed on the user's computer system.

These include:
- requests
- uk_covid19
- flask
- webbrowser
- pytest

### - Config File

To configure the possible variables on the dashboard, use the **config.json** file.

Within this file, users will find the ability to alter:
- Local Location
- National Location
- Amount of news articles displayed
- News articles keywords
- News article dates
- News API key

Simply edit the values and saving the file is all that is required to update any preferences.

### - News API Key

Required for the news articles in this dashboard is a news API key.
A free one can be retrieved by signing up to **newsapi.org**.
Once this has been obtained, the user must then enter this into the aforementioned config file.

### - Log File

The text file **logFile.txt** will initially be empty after first download. Anytime the dashboard is run, any events, or
errors will be logged to this file and can be examined freely by the user.

## - Deleted Articles File

The text file **deletedArticles.txt** will initially be empty after first download. When an article is deleted from
the dashboard UI, it is written into this text file so that even after the application is closed, the same article
will never reappear on the user's dashboard. If a user mistakenly deletes an article, they can remove it from this text
file, allowing it to once again be shown.

### - Launching the App

The app can be launched simply by running the main code, the webpage containing
the dashboard is automatically opened in a new tab on your default browser.

### - Controlling News Articles

As previously mentioned, the amount of articles displayed, the keywords and date
used for the searching of articles can be configured in the config file.

If an invalid configuration of keywords, date
or API key is submitted, the dashboard will run, but display a message in place
of the news articles alerting the user to this error.

Whilst the dashboard is running, the user is also provided with the ability
to delete articles, such articles will be permanently excluded from the article search.

### - Configuring Updates

Using the controls provided in the UI, the user can set updates for a
certain time point in the future.

By selecting different options, the user can configure:
- Whether or not the update will update the covid-data
- Whether or not the update will update the news articles
- Whether or not the update will repeat at the same time every 24 hour period

The time entered for the update to occur must be a valid and in 24 hour
format, otherwise, the update will not be queued. If a time entered is
an earlier time to the current time, the update will be set for that time on the next day.

### - Deleting Updates

Updates can be deleted in the same manner that news articles can. Once an update is
deleted, the scheduled data update will be cancelled and the update will disappear.

If left to run, the update will update the values and then delete itself from the
dashboard, unless it is a repeating update, for which an update is simply rescheduled for the
same time the next day.

### - Closing the App

The app can be stopped by closing the python window that is running. After this has been terminated,
the web page will no longer run.

## Developer Documentation

Listed below is detailed documentation on how the code works and a breakdown
of the different functions and modules involved.

### - Modules

The dashboard is comprised of 3 main modules:
- **covid_data_handler.py** - Responsible for communicating with the covid data API.
- **covid_news_handling.py** - Responsible for communicating with the news API and 
formatting news articles.
- **main.py** - The main code, collecting information from the two other modules and
then hosts the data on the flask interface. Also responsible for handling user communications
with the flask interface.

### - Algorithms

All algorithms are explained in more detail with examples in the docstrings of the function
itself.

#### > covid_data_handler.py

- **parse_csv_data** > Takes the name of a file in a the form of a string and returns a list
of all the rows from the csv file.
- **process_covid_csv_data** > Takes a list of rows from a csv file and processes it into
a list of covid cases, hospital cases and cumulative deaths.
- **covid_API_request** > Takes a string of a location and location type that an API request
is is then made for. The resultant values are then taken and returned in a dictionary,
with the keyword being the name of the category of data.
- **get_new_covid_data** > Takes a dictionary containing the location name and area type for both
a local and national location of the desired API request. Will then call the covid_API_request for each
location and store the data in the global covid_data variable.
- **schedule_covid_updates** > Takes a float of the amount of seconds until the update and a string
of the update name. Will then place the **get_new_covid_data** function on the scheduler queue for the
desired time interval. Returns the class for the event that was queued.
- **find_first_value** > Takes a list and an example of a null value and will return the index of the
first value in the list that is not a null value.
- **create_list_from_dict** > Takes a list of dictionaries and keyword that it is desired to be extracted
from each dictionary in the list. Returns a list containing all the extracted values from the specified
keyword from each dictionary in the list.
- **attempt** > Takes a list of dictionaries, the keyword for the desired element and an example of a null value.
Returns the first non-null value of the values from the list of dictionaries.

#### > covid_news_handling.py

- **news_API_request** > Takes a string of keyword terms and then makes a request to the news API. Will return
the response in a dictionary.
- **select_articles** > Takes a dictionary of data which contains the article data as well as an integer value
which represents how many articles are desired. Will then sort through the data, adding the correct number of articles
to a list, ignoring any articles contained on **deletedArticles.txt**. Returns a list of dictionaries, with each dictionary
being an article and its attributes.
- **get_new_articles** > Takes a dictionary of arguments (that have been extracted from the config file). Makes an API request
with these arguments and uses the response to update the global news_articles.
- **update_news** > Takes a string of the update name and a float containing the delay time before the update. Enters
**get_new_articles** onto the scheduler to occur after the given interval. Returns the class of the event that was
scheduled.
- **delete_article** Takes an integer index and a list of articles and will write the article at the position of
the index into **deletedArticles.txt**. Will NOT delete the article from the list itself.

#### > main.py

- **home** > A flask subroutine that places the current data into the flask template and posts it.
Accessed when the web page route is '/'.
- **update** > A flask subroutine that is accessed when the web page route changes from the base '/'.
Is the subroutine responsible for recognising and dealing with any of the updates made by the user
to the web page, such as inputting an update request or deleting an update/article. The sufficient
function to handle the request is then called subsequently. Subroutine then redirects the web page
to the **home** subroutine for any updates to be posted.
- **init_data** > Initialises the data for when the application starts, making all required requests
to APIs and creates a dictionary out of the formatted data. This dictionary is returned.
- **check_for_updates** > When called, will check with both schedules if an update should have occurred.
If so, it will update the neccessary data values.
- **delete_update** > Takes the name of the deleted update as a string and will search through the current
list of updates. The update desired to be deleted will have corresponding events on the scheduler cancelled
as well as termination of itself.
- **update_covid_data** > Will check the **covid_data_handler.py** to see if new data values
have been determined. These new values will be copied into the data dictionary so that they
can be posted to the flask template next iteration.
- **update_articles** > Will check the **covid_news_handling.py** to see if new articles
have been fetched. These new articles will be copied into the data dictionary so that they
can be posted to the flask template next iteration.
- **check_for_complete_updates** > Checks to see if an existing update has occurred and if so, will delete
the update from the user interface. If the update that has been completed is found to be a repeating update,
it is not deleted from the UI, and the **do_repeat_update** subroutine is called.
- **do_repeat_update** > Updates that have been completed but are classed as repeating are rescheduled
for the same time the next day and the values for the update are changed accordingly.
- **search_articles** > Takes a list of articles and a string containing the name of the target title.
Returns the index of the position in the list of the target title.
- **get_time_until** > Takes a string of the time wanted in the format HH:MM and returns a float of the number of
minutes until that point in time from the current point in time.
- **create_update_content** > Takes a series of variables related to an update and returns a suitable string
containing information about the update that can be used for the 'content' of the update.

### Testing

Sufficient testing for the third-party aspects of this project can be found in:
- **test_covid_data_handler.py**
- **test_covid_news_handling.py**

Running these tests on their own will independently assess the validity of the API requests among other functions.
These tests can also be run using the pytest module. This is done via the command line and can be done at any
point to test the validity of the data.


## Creator Details

- **Author**: Samuel Menary
- **Email**: sjm269@exeter.ac.uk
- **GitHub Link**: https://github.com/Sam-Menary/ECM1400-Covid-Dashboard-Project
