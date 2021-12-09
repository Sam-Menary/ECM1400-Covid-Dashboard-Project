import requests
import json
import datetime
import sched
import time
import logging


news_articles = []
news_sched = sched.scheduler(time.time, time.sleep)


def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:
    """
    Make a request to the news API.

    A request is made to the news API, based on the given covid terms
    and the 'date from' contained in the config file. Will return a
    dictionary of the desired articles returned from the news API
    request.

    Parameters
    ----------
    covid_terms : str, default 'Covid COVID-19 coronavirus'
        The keyword terms for the desired articles.

    Returns
    -------
    response.json() : dict
        A dictionary containing the result of the news API request.

    See Also
    --------
    select_articles : Takes the return from the news_API_request and
        sorts through the articles for the amount of articles desired
        as well as the desired data from each article.

    Examples
    --------
    >>> news_articles = news_API_request('omnicron')
    """
    base_url = 'https://newsapi.org/v2/everything?'
    data = json.load(open('config.json'))
    api_key = '&apiKey='+str(data["apiKey"])
    date_from = data["newsArgs"]["dateFrom"]
    if date_from == "current":
        date_wanted = str(datetime.date.today()-datetime.timedelta(days=1))
    else:
        date_wanted = date_from
    restrictions = '&from='+date_wanted+'&sortBy=popularity'
    complete_url = base_url+'q='+covid_terms+restrictions+api_key
    response = requests.get(complete_url)
    logging.debug("News API request made for articles with keywords " +
                  covid_terms+" from "+str(date_wanted))
    return(response.json())


def select_articles(article_data: dict, article_count: int) -> list:
    """
    Select the desired amount of articles from the news API request.

    Takes in the return from news_API_request and will sort through
    for the desired articles, comparing each to the text file of
    deleted articles, which are the articles the user does not wish
    to see. For each article that is chosen, the desired data is
    extracted and placed in a list consisting of a dictionary for
    each article.

    Parameters
    ----------
    article_data : dict
        The keyword terms for the desired articles.
    article_count : int
        The amount of articles the user desires.

    Returns
    -------
    articles : list
        A list of dictionaries, with each dictionary being a chosen
        article.

    See Also
    --------
    news_API_request : Makes the request to the news API and the return
        should be used as the input to this function.
    get_new_articles : Uses selec_articles function to update the global
        news_articles with new article data.

    Examples
    --------
    >>> news_articles = news_API_request('omnicron')
    >>> list_of_articles = select_articles(news_articles, 3)
    """
    with open('deletedArticles.txt') as file:
        lines = file.readlines()
    file.close()
    deleted_articles = []
    if len(lines) > 1:
        for i in range(len(lines)):
            deleted_articles.append(lines[i][0:len(lines[i])-1])
    x = article_data["articles"]
    articles = []
    index = 0
    while len(articles) < article_count and index < len(x):
        article = True
        for j in range(len(deleted_articles)):
            if str(x[index]["title"])+','+str(x[index]["author"]) == \
               deleted_articles[j]:
                article = False
        if article:
            return_dict = {}
            return_dict["author"] = x[index]["author"]
            return_dict["title"] = x[index]["title"]
            return_dict["content"] = x[index]["description"]
            return_dict["url"] = x[index]["url"]
            return_dict["date"] = x[index]["publishedAt"]
            articles.append(return_dict)
        index += 1
    logging.debug(str(len(articles)) +
                  " Article(s) successfully selected from news API request")
    return(articles)


def get_new_articles(arguments: dict):
    """
    Update the global news_articles with new data.

    Works in tandem with the select_articles and news_API_request to
    update the global news_articles with a list of dictionaries
    containing up-to-date articles.

    Parameters
    ----------
    arguments : dict
        The dictionary containing the article count and keyword terms,
        ideally gathered from the config file.

    See Also
    --------
    select_articles : Takes the return from the news_API_request and
        sorts through the articles for the amount of articles desired
        as well as the desired data from each article.
    update_news : Is used to schedule calls of the get_news_article
        function at intervals for which the user decides.

    Examples
    --------
    >>> news_articles = get_new_articles(
    ...     {
    ...         "terms": "Omnicron",
    ...         "articleCount": 3
    ...     }
    ... )
    """
    global news_articles
    article_terms = str(arguments["terms"])
    article_count = int(arguments["articleCount"])
    try:
        request_data = news_API_request(article_terms)
        news_articles = select_articles(request_data, article_count)
        logging.info("News articles update successful")
    except:
        news_articles = [
            {
                "title": 'ERROR: No articles avalible at this time',
                "content": 'Invalid API key, keywords or time was entered'
            }
        ]
        logging.error("Invalid API key, keywords or time was entered")
    if len(news_articles) == 0:
        news_articles = [
            {
                "title": 'ERROR: No articles avalible at this time',
                "content": 'No articles were found for the given keywords \
                            at this time'
            }
        ]
        logging.error("No news articles to be found at this time")


def update_news(update_name: str, update_interval: float = 5.0):
    """
    Schedule a news article update.

    A news article update is scheduled for a desired amount of seconds
    in the future. This update will update the global news_articles.
    It will gather the neccessary information such as desired article
    terms and number of articles from the config file.

    Parameters
    ----------
    update_interval : float
        The amount of seconds until the update is desired to occur.
    update_name : str
        The name of the update.

    Returns
    -------
    event : class
        A class of the news article update event that has been placed
        onto the scheduler.

    See Also
    --------
    get_new_articles : The function that is placed on the scheduler,
        it will update the global news_articles with new articles
        from the news API request.

    Examples
    --------
    >>> news_update_event = update_news(10, 'new update')
    """
    try:
        config_args = json.load(open('config.json'))["newsArgs"]
    except:
        print("invalid formatting on the config file")
    event = news_sched.enter(update_interval,
                             1,
                             get_new_articles,
                             (config_args,))
    logging.debug("News article update scheduled for " +
                  str(update_interval)+"s time")
    return(event)


def delete_article(index: int, articles: list):
    """
    Store the name of deleted article in a file.

    The name and author of a given article, which is identified from
    the list of articles from the index, is written into a text file
    which contains all of the deleted articles selected by the user.
    Note that this does not delete the article from the list itself,
    it simply writes the name and author to a file so that the
    select_articles function knows which articles not to choose.

    Parameters
    ----------
    index : int
        The numerical list index of the desired article to delete.
    articles : list
        The list of articles, from which the article will have the name
        written into a file.

    Examples
    --------
    >>> articles = [{"title": "articlce", "author": "name"}]
    >>> delete_article(0, articles)
    """
    file = open('deletedArticles.txt', 'a')
    title = articles[index]["title"]
    author = articles[index]["author"]
    text = str(title)+','+str(author)+'\n'
    try:
        file.write(text)
    except:
        logging.error("Failed to write article to deletedArticles.txt due to \
unknown unicode char")
    file.close()
