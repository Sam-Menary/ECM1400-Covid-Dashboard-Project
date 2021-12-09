import sched
import time
import flask
import covid_data_handler
import covid_news_handling
import webbrowser
import csv
import datetime
import json
import logging
import pytest


data = {}


app = flask.Flask(__name__)
log = logging.getLogger(__name__)
log_format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s'
logging.basicConfig(filename='logFile.txt',
                    filemode='a',
                    format=log_format,
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger('werkzeug').disabled = True
logging.getLogger('urllib3.connectionpool').disabled = True


@app.route('/')
def home():
    """
    Post data to web page template.

    Data is gathered and updated and then posted to the web page
    using the flask.render_template function.

    See Also
    --------
    check_for_updates : Checks to see if a scheduled event should have
        happened and will update global covid_data and news_articles
        accordingly.
    """
    global data
    check_for_updates()
    local = data["location"]["local"]["name"]
    national = data["location"]["national"]["name"]
    return flask.render_template('index.html',
                                 title='Covid Dashboard',
                                 location=local,
                                 nation_location=national,
                                 local_7day_infections=
                                 data["local_infections"],
                                 national_7day_infections=
                                 data["national_infections"],
                                 hospital_cases=
                                 "National Hospital Cases: " +
                                 str(data["hospital_cases"]),
                                 deaths_total="National Death Toll: " +
                                 str(data["cumulative_deaths"]),
                                 news_articles=data["articles"],
                                 updates=data["updates"],
                                 image='logo.png')


@app.route('/<index>')
def update(index):
    """
    Check for, schedule and delete updates + articles.

    Updates made to the web page are detected and dealt with
    accordingly. If the a news article is deleted, it is carried out
    here, updates are scheduled and deleted here also. The updates are
    carried out and then the website is re-directed to the home page,
    where the new data is posted into the html template.
    """
    global data
    if 'notif' in flask.request.args:
        article_name = flask.request.args.get('notif')
        if flask.request.args.get('notif') != 'ERROR: No articles found':
            try:
                article_index = search_articles(data["articles"], article_name)
                covid_news_handling.delete_article(
                    article_index,
                    data["articles"]
                    )
                logging.info("Deleted article: '"+article_name+"'")
                data["articles"].pop(article_index)
            except:
                logging.error("Delete was called with no articles to delete")
    elif 'two' in flask.request.args and 'update' in flask.request.args:
        if flask.request.args.get('update') != '':
            update_name = flask.request.args.get('two')
            for i in range(len(data["updates"])):
                if data["updates"][i]["title"] == update_name:
                    logging.error("Update with a duplicate title was entered")
            update_time = flask.request.args.get('update')
            time_until_update = get_time_until(update_time)
            current_date = datetime.datetime.today().strftime('%Y-%m-%d')
            update_date = current_date.split("-")
            if time_until_update < 0:
                time_until_update += 1440
                new_day = str(int(update_date[2])+1)
                if len(new_day) == 1:
                    new_day = '0'+new_day
                update_date[2] = new_day
            update_covid = False
            update_news = False
            repeat = False
            events = []
            if 'covid-data' in flask.request.args:
                update_covid = True
                covid_event = covid_data_handler \
                    .schedule_covid_updates(time_until_update*60, update_name)
                events.append(covid_event)
            if 'news' in flask.request.args:
                update_news = True
                news_event = covid_news_handling \
                    .update_news(update_name, time_until_update*60)
                events.append(news_event)
            if 'repeat' in flask.request.args:
                repeat = True
            content = create_update_content(update_date,
                                            update_time,
                                            update_covid,
                                            update_news,
                                            repeat)
            new_update = {
                'title': update_name,
                'content': content,
                'covidData': update_covid,
                'news': update_news,
                'events': events,
                'repeat': repeat,
                'updateTime': update_time,
                'updateDate': update_date
                }
            data["updates"].append(new_update)
            logging.info("Set update '"+update_name +
                         "' for "+str(update_time)+' on '+str(update_date))
        else:
            logging.error("Invalid time was entered for update")
    elif 'update_item' in flask.request.args:
        update_name = flask.request.args.get('update_item')
        try:
            delete_update(update_name)
        except:
            logging.error("Delete was called with no update to delete")
    return flask.redirect('/')


def init_data() -> dict:
    """
    Initalise data required for the application.

    Data is initalised from each independent API request and stored in
    the neccessary parts of the data_dictionary so that they can be
    accessed correctly when the data is extracted and posted into
    the HTML template.

    Returns
    -------
    data_dict : dict
        A dictionary containing all the values required for the
        application to function.
    """
    data_dict = {"location": {}}
    config_data = json.load(open('config.json'))
    data_dict["location"]["local"] = config_data["location"]["local"]
    data_dict["location"]["national"] = config_data["location"]["national"]
    covid_news_handling.get_new_articles(config_data["newsArgs"])
    covid_data_handler.get_new_covid_data(config_data["location"])
    data_dict["updates"] = []
    logging.info("Initalised data succesfully")
    return(data_dict)


def check_for_updates():
    """
    Check for updates to the global covid_data and news_articles.

    Both the covid-data schedules and the news article schedule are
    checked independently to see if an update has occured since the
    last time it checked. The covid-data and news articles are then
    updated with the new data.

    See Also
    --------
    check_for_complete_updates : Checks to see if (based on the curren
        time) an update should have happened, and if so, it will either
        delete the update from the updates list or will re-queue the
        update if the given update is a repeating one.
    """
    covid_data_handler.covid_sched.run(blocking=False)
    covid_news_handling.news_sched.run(blocking=False)
    update_covid_data()
    update_articles()
    check_for_complete_updates()


def delete_update(cancelled_update: str):
    """
    Delete an update based on a given index.

    An update is deleted prematurely by the user and so the events
    scheduled originally for new data is cancelled and the update
    itself is deleted from the global data dictionary so that it is
    no longer posted by flask application.

    Parameters
    ----------
    cancelled_update : str
        A string containing the name of the update.
    """
    global data
    update_index = search_articles(data["updates"], cancelled_update)
    update = data["updates"][update_index]
    if update["covidData"]:
        covid_data_handler.covid_sched.cancel(update["events"][0])
    if update["news"]:
        index = 1
        if len(update["events"]) == 1:
            index = 0
        covid_news_handling.news_sched.cancel(update["events"][index])
    update_name = update["title"]
    data["updates"].pop(update_index)
    logging.info("Deleted update: '"+update_name+"'")


def update_covid_data():
    """
    Update the global data dictionary with new values from the API.

    The global data dictionary is passed the values from the global
    covid_data, in effect updating the variables with new data from
    the API request.
    """
    global data
    new_local_data = covid_data_handler.covid_data[0]
    new_national_data = covid_data_handler.covid_data[1]
    data["local_infections"] = new_local_data["covidCases"]
    data["national_infections"] = new_national_data["covidCases"]
    data["hospital_cases"] = new_national_data["hospitalCases"]
    data["cumulative_deaths"] = new_national_data["cumulativeDeaths"]


def update_articles():
    """
    Update the global data dictionary with new values from the API.

    The global data dictionary is passed the values from the global
    news_articles, in effect updating the articles with new data from
    the API request.
    """
    global data
    data["articles"] = covid_news_handling.news_articles


def check_for_complete_updates():
    """
    Check for any completed updates based on the current time.

    Any updates that should have occured are removed based on the
    time they have associated with them. This time is compared to the
    current time and updates are deleted accordingly. Any update that
    is deemed to have already occured but is also found to be
    repeating update is then scheduled to repeat using the
    do_repeat_update function.

    See Also
    --------
    do_repeat_update : Will re-schedule a repeating update for 24 hours
        time, updating neccessary values attributed to this.
    """
    global data
    update_remove_queue = []
    for i in range(len(data["updates"])):
        current_time = datetime.datetime.now().strftime("%H:%M:%S").split(':')
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')
        update_time = data["updates"][i]["updateTime"].split(':')
        if current_date.split('-') == data["updates"][i]["updateDate"]:
            if current_time[0] >= update_time[0]:
                if current_time[1] >= update_time[1]:
                    if data["updates"][i]["repeat"]:
                        do_repeat_update(i)
                    else:
                        update_remove_queue.append(i)
    for i in reversed(sorted(update_remove_queue)):
        logging.info("Cleared update: '"+data["updates"][i]["title"]+"'")
        data["updates"].pop(i)


def do_repeat_update(index: int):
    """
    Repeat an update based off an index passed in as a parameter.

    The update indentified by the index passed in is set for 24 hours
    time, updating the updateDate and content so that it aligns
    with the update being set for the next day.

    Parameters
    ----------
    index : int
        The integer index value of the selected update that is to be
        repeated.
    """
    global data
    next_update = get_time_until(data["updates"][index]["updateTime"])
    next_update = next_update+1440
    next_date = data["updates"][index]["updateDate"]
    next_day = str(int(next_date[2])+1)
    if len(next_day) == 1:
        next_day = '0'+next_day
    next_date[2] = next_day
    update_name = data["updates"][index]["title"]
    data["updates"][index]["events"] = []
    if data["updates"][index]["covidData"]:
        covid_event = covid_data_handler \
                      .schedule_covid_updates(next_update*60, update_name)
        data["updates"][index]["events"].append(covid_event)
    if data["updates"][index]["news"]:
        news_event = covid_news_handling \
                     .update_news(update_name, next_update*60)
        data["updates"][index]["events"].append(news_event)
    data["updates"][index]["updateDate"] = next_date
    new_content = create_update_content(data["updates"][index]["updateDate"],
                                        data["updates"][index]["updateTime"],
                                        data["updates"][index]["covidData"],
                                        data["updates"][index]["news"],
                                        data["updates"][index]["repeat"])
    data["updates"][index]["content"] = new_content
    logging.info("Repeating Update: '"+data["updates"][index]["title"] +
                 "' on "+str(data["updates"][index]["updateDate"]))


def search_articles(articles: list, target_title: str) -> int:
    """
    Search through a list of dictionaries for a specific string title.

    A list of dictionaries is iterated through and the title of each
    dictionary is compared to the title passed in as a parameter.
    The list index of the desired article is returned.

    Parameters
    ----------
    articles : list
        A list of dictionaries that is desired to be searched.
    target_title : string
        A string containing the name of the desired article.

    Returns
    -------
    index : int
        The integer value of the list index of the desired article.
    """
    index = -1
    for i in range(len(articles)):
        if articles[i]["title"] == target_title and target_title is not None:
            index = i
    return(index)


def get_time_until(end_time: str) -> float:
    """
    Evalute the time until a desired time from the current time.

    The amount of minutes until a certain point of time from the
    current time is calculated and returned, rounded to 1 decimal place.

    Parameters
    ----------
    end_time : str
        The time that it is desired to find the difference between,
        in the format hh:mm.

    Returns
    -------
    time_until : float
        The value in minutes of the difference between the current
        time and the time desired.
    """
    current_time = datetime.datetime.now().strftime("%H:%M:%S").split(':')
    difference = []
    for i in range(2):
        difference.append(int(end_time.split(':')[i])-int(current_time[i]))
    time_until = difference[0]*60+difference[1]-int(current_time[2])/60
    return(round(time_until, 1))


def create_update_content(date, time, update_data, update_news, repeat):
    """
    Create text content for an update based on parameters.

    A string for the content of an update is evaluated based on
    varying parameters, like when the update is happening, what the
    update is updating and whether or not the update will repeat.

    Parameters
    ----------
    date : list
        A list containing the day, month and year of the update.
    time : str
        A str of the time the update will occur, in the format
        hh:mm.
    update_data : bool
        A bool vlaue of whether or not the update will update
        covid-data values.
    update_news : bool
        A bool value of whether or not the update will update
        news articles.
    repeat : bool
        A bool value of whetehr or not the update will repeat.

    Returns
    -------
    text : str
        A string of the text that is to be used as the update
        content.
    """
    date = date[2]+"/"+date[1]+"/"+date[0]
    text = "Update set for "+str(time)+" on "+str(date)+". "
    if update_news and update_data:
        text = text+"Will update covid-data and news. "
    elif update_news:
        text = text+"Will update news. "
    elif update_data:
        text = text+"Will update covid-data. "
    if repeat:
        text = text+"Update will repeat."
    return(text)


if __name__ == '__main__':
    data = init_data()
    webbrowser.open('http://127.0.0.1:5000/', new=2)
    app.run()
