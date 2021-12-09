import covid_news_handling
from covid_news_handling import news_API_request
from covid_news_handling import select_articles
from covid_news_handling import get_new_articles
from covid_news_handling import update_news
from covid_news_handling import delete_article


def test_news_API_request():
    """
    Checks that the news_API_request can be called succesfully and
    has defualt values 'Covid COVID-19 coronavirus'.
    """
    assert news_API_request()
    assert news_API_request('Covid COVID-19 coronavirus') == news_API_request()


def test_select_articles():
    """
    Checks that the number of chosen articles is the same as the amount
    of articles returned form the select_articles function.
    """
    article_count = 2
    article_data = news_API_request()
    articles = select_articles(article_data, article_count)
    if len(article_data["articles"]) >= article_count:
        assert len(articles) == article_count
    elif len(article_data["articles"]) > 0 and \
         len(article_data["articles"]) < article_count:
        assert len(articles) == len(article_data["articles"])
    else:
        assert len(articles) == 0


def test_get_new_articles():
    """
    Checks that the global variable news_articles is updated  to the
    correct values when get_new_articles is called.
    """
    if __name__ == "__main__":
        assert covid_news_handling.news_articles == []
    terms = 'Covid COVID-19 coronavirus'
    article_count = 2
    articles = select_articles(news_API_request(terms), article_count)
    args = {"terms": terms, "articleCount": article_count}
    get_new_articles(args)
    if len(articles) > 0:
        if len(articles) >= article_count:
            assert len(covid_news_handling.news_articles) == article_count
        else:
            assert len(covid_news_handling.news_articles) == len(articles)
        for i in range(len(covid_news_handling.news_articles)):
            assert covid_news_handling.news_articles[i]["title"] == \
                   articles[i]["title"]
    else:
        assert len(covid_news_handling.news_articles) == 0


def test_update_news():
    """
    Checks that the update_news function succesfully schedules
    an update.
    """
    update_news('test')


def test_delete_article():
    """
    Checks that the delete_article function correctly writes the
    elected article into the deletedArticles text file.
    """
    article = {"title": "test article", "author": "test author"}
    articles = [article]
    delete_article(0, articles)
    file = open('deletedArticles.txt', 'r')
    deleted_item = file.read().splitlines()[-1]
    file.close()
    text = str(article["title"])+','+str(article["author"])
    assert deleted_item == text


if __name__ == "__main__":
    test_news_API_request()
    test_select_articles()
    test_get_new_articles()
    test_update_news()
    test_delete_article()
    print("Tests Cleared")
