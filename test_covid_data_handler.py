import covid_data_handler
import pytest
from covid_data_handler import parse_csv_data
from covid_data_handler import process_covid_csv_data
from covid_data_handler import covid_API_request
from covid_data_handler import get_new_covid_data
from covid_data_handler import schedule_covid_updates
from covid_data_handler import find_first_value
from covid_data_handler import create_list_from_dict
from covid_data_handler import attempt


def test_parse_csv_data():
    """
    Checks that the length of the parsed csv file is the correct length.
    """
    data = parse_csv_data('nation_2021-10-28.csv')
    assert len(data) == 639


def test_process_covid_csv_data():
    """
    Checks that the processed values are correct.
    """
    last7days_cases , current_hospital_cases , total_deaths = \
        process_covid_csv_data ( parse_csv_data (
            'nation_2021-10-28.csv' ) )
    assert last7days_cases == 240_299
    assert current_hospital_cases == 7_019
    assert total_deaths == 141_544


def test_covid_API_request():
    """
    Checks that the API makes a request and that the request returns
    a dictionary.
    """
    data = covid_API_request()
    assert isinstance(data, dict)


def test_get_new_covid_data():
    """
    Checks that the global covid_data is updated with the correct values
    that are returned from the API request.
    """
    if __name__ == "__main__":
        assert covid_data_handler.covid_data == []
    local = {"name": "Exeter", "areaType": "ltla"}
    national = {"name": "England", "areaType": "nation"}
    locations = {"local": local, "national": national}
    local_data = covid_API_request(local["name"], local["areaType"])
    national_data = covid_API_request(national["name"], national["areaType"])
    get_new_covid_data(locations)
    assert len(covid_data_handler.covid_data) == 2
    assert covid_data_handler.covid_data[0]["covidCases"] == \
           local_data["covidCases"]
    assert covid_data_handler.covid_data[1]["covidCases"] == \
           national_data["covidCases"]


def test_schedule_covid_updates():
    """
    Checks that a covid data update can be scheduled.
    """
    schedule_covid_updates(update_interval=10, update_name='update test')


def test_find_first_value():
    """
    Checks that the value returned for the first value is correct.
    """
    l = [0, 0, 0, 10, 15, 3]
    first_value = 3
    assert find_first_value(l, 0) == first_value


def test_create_list_from_dict():
    """
    Checks that each element in the list is correctly mapped to the
    list of dictionaries.
    """
    dict_list = []
    for i in range(5):
        dict_list.append({"number": i})
    l = create_list_from_dict(dict_list, "number")
    for i in range(len(dict_list)):
        assert l[i] == dict_list[i]["number"]


def test_attempt():
    """
    Checks that the value is correctly found from the list of
    dictionaries and checks that the function will return 'No Data'
    for occasions where there is no data.
    """
    dict_list = []
    for i in range(5):
        dict_list.append({"number": i})
    assert attempt(dict_list, "number", 0) == 1
    dict_list = []
    for i in range(5):
        dict_list.append({"number": ''})
    assert attempt(dict_list, "number", '') == "No Data"


if __name__ == "__main__":
    test_parse_csv_data()
    test_process_covid_csv_data()
    test_covid_API_request()
    test_get_new_covid_data()
    test_schedule_covid_updates()
    test_find_first_value()
    test_create_list_from_dict()
    test_attempt()
    print("Tests Cleared")
