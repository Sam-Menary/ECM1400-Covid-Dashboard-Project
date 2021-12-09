import csv
import time
import requests
import json
import sched
import logging
import uk_covid19


covid_data = []
covid_sched = sched.scheduler(time.time, time.sleep)


def parse_csv_data(csv_filename: str) -> list:
    """
    Parse csv data from a file.

    The csv file is read line by line and the resulting data
    is placed into a list. Each element in the returned list
    is a list containing all the cells from each collumn.

    Parameters
    ----------
    csv_filename : str
        The name of the csv file.

    Returns
    -------
    rows : list
        List containg all the data from the csv file.

    See Also
    --------
    process_covid_csv_data : Will process the data that is
        extracted in this function.

    Examples
    --------
    >>> list = parse_csv_data('filename.csv')
    """
    lines = csv.reader(open(csv_filename))
    rows = []
    for row in lines:
        rows.append(row)
    logging.info("CSV data from "+csv_filename+" successfully parsed")
    return(rows)


def process_covid_csv_data(covid_csv_data: list) -> list:
    """
    Process covid data from a csv file.

    The data is taken in an interpreted in accordance with the
    required covid data.

    Parameters
    ----------
    covid_csv_data : list
        The list containing the covid csv data that is to be processed.

    Returns
    -------
    return_list : list
        A list of the neccessary covid data values that has been
        processed by the function.

    See Also
    --------
    parse_csv_data : Collects the data from a csv and returns it as a
    list.

    Examples
    --------
    >>> csv_rows = parse_csv_data('filename.csv')
    >>> covid_data = process_covid_csv_data(csv_rows)
    """
    identifier_dict = {}
    for i in range(len(covid_csv_data[0])):
        identifier_dict[covid_csv_data[0][i]] = i
    covid_csv_data.pop(0)
    return_list = []
    try:
        covid_cases_index = identifier_dict["newCasesBySpecimenDate"]
        data_list = create_list_from_dict(covid_csv_data, covid_cases_index)
        start_index = find_first_value(data_list, '')
        covid_cases = 0
        for i in range(start_index+1, start_index+8):
            covid_cases += int(covid_csv_data[i][6])
        return_list.append(covid_cases)
        hospital_cases_index = identifier_dict["hospitalCases"]
        return_list.append(int(attempt(covid_csv_data,
                                       hospital_cases_index, '')))
        deaths_index = identifier_dict["cumDailyNsoDeathsByDeathDate"]
        return_list.append(int(attempt(covid_csv_data,
                                       deaths_index, '')))
        logging.info("CSV data successfully processed")
    except:
        logging.error("CSV file has insufficient/incorrectly named data")
    return(return_list)


def covid_API_request(location='Exeter', location_type='ltla') -> dict:
    """
    Make a request to the covid API.

    A request is made to the covid API, based on the given location
    and area type. Will return a dictionary of the desired values.

    Parameters
    ----------
    location : str, default 'Exeter'
        The name of the location desired.
    location_type : str, defualt 'ltla'
        The area type of the desired location.

    Returns
    -------
    return_dict : dict
        A dictionary of the desired values gathered from the API.

    See Also
    --------
    get_new_covid_data : Will call the covid_API_request function
        for each desired location and will update global covid_data
        with the returns.

    Examples
    --------
    >>> covid_data = covid_API_request(locationName, areaType)
    """
    area_filter = [
        'areaType='+location_type,
        'areaName='+location
    ]
    structure = {
        "date": "date",
        "newCases": "newCasesBySpecimenDate",
        "cumDeaths": "cumDailyNsoDeathsByDeathDate",
        "hospitalCases": "hospitalCases"
    }
    api_request = uk_covid19.Cov19API(filters=area_filter, structure=structure)
    data = api_request.get_json()
    x = data["data"]
    return_dict = {}
    covid_cases = 0
    start_index = find_first_value(create_list_from_dict(x, "newCases"), None)
    for i in range(start_index, start_index+7):
        covid_cases += int(x[i+1]["newCases"])
    return_dict["covidCases"] = covid_cases
    return_dict["hospitalCases"] = attempt(x, "hospitalCases", None)
    return_dict["cumulativeDeaths"] = attempt(x, "cumDeaths", None)
    logging.debug("Covid API request made for "+location)
    return(return_dict)


def get_new_covid_data(locations: dict):
    """
    Update covid data for desired locations with new data.

    An API request is made for both local and national areas and
    the returns are used to update the current global covid_data.

    Parameters
    ----------
    locations : dict
        A dictionary containg the name and area type for both national
        and local locations.

    See Also
    --------
    covid_API_request : The function used to make the actual API
        request for the specified locations.
    schedule_covid_upates : Will enter get_new_covid_data into
        the scheduler queue based on a desired update_interval.
    """
    global covid_data
    covid_data = []
    covid_data.append(covid_API_request(locations["local"]["name"],
                                        locations["local"]["areaType"]))
    covid_data.append(covid_API_request(locations["national"]["name"],
                                        locations["national"]["areaType"]))
    logging.info("Covid-data update successful")


def schedule_covid_updates(update_interval: float, update_name: str):
    """
    Schedule an update for covid data.

    An update for the global covid_data is scheduled for a specified
    amount of time in the future. The event that has been scheduled
    is returned. Gathers neccessary information such as the loction
    names and area types from the config file.

    Parameters
    ----------
    update_interval : float
        The amount of seconds until the update is desired to occur.
    update_name : str
        The name of the update.

    Returns
    -------
    event : class
        A class of the covid data update event that has been placed
        onto the scheduler.

    See Also
    --------
    get_new_covid_data : The function that is placed on the scheduler,
        it will update the global covid_data with new values from the
        API request.

    Examples
    --------
    >>> covid_update_event = schedule_covid_updates(10, 'new update')
    """
    config_locations = json.load(open('config.json'))["location"]
    event = covid_sched.enter(update_interval,
                              1,
                              get_new_covid_data,
                              (config_locations,))
    logging.debug("Covid-data update scheduled for " +
                  str(update_interval)+"s time")
    if __name__ == "__main__":
        covid_sched.run()
    return(event)


def find_first_value(array: list, reject_statement) -> int:
    """
    Find the first non-blank value in a list.

    The first value which is not 'blank', in accordance with the
    reject_statement will be identified and returned.


    Parameters
    ----------
    array : list
        The list that will be searched for the first blank value.
    reject_statement : list OR str OR int OR float OR bool
        A value that is used to identify what is classed as a blank
        element.

    Returns
    -------
    index : int
        The index value of the first non-blank value in the submitted
        array.

    Examples
    --------
    >>> l = ['', '', '', 'data']
    >>> index = find_first_value(l, '')
    >>> index
    >>> 3
    """
    index = len(array)+1
    for i in range(len(array)):
        if array[i] != reject_statement and i < index:
            index = i
    if index > len(array):
        index = 'not valid'
    return(index)


def create_list_from_dict(list_of_dictionaries: list, element: str) -> list:
    """
    Create a list from the values in a list of dictionaries.

    A list is returned which is comprised of all the items from a
    specific index in a lsit of dictionaries.

    Parameters
    ----------
    list_of_dictionaries : list
        A list of dictionaries for which a certain element is desired
        to be extracted from each dictionary.
    element : str
        The key of the desired element from the dictionaries that
        is to be extracted.

    Returns
    -------
    new_list : list
        The list comprised of all the desired elements from the list of
        dictionaries.

    Examples
    --------
    >>> l = [{"name": "John", "age": 56}, {"name": "Mike", "age": 35}]
    >>> new_list = create_list_from_dict(l, "age")
    >>> new_list
    >>> [56,35]
    """
    new_list = []
    for i in range(len(list_of_dictionaries)):
        new_list.append(list_of_dictionaries[i][element])
    return(new_list)


def attempt(data: list, query: str, reject_statement):
    """
    Attempt to get certain data from a list of values.

    Desired data is attempted to be found in a list by finding the first
    non-blank value and returning it. If a value cannot be found,
    "No data" is returned instead.

    Prameters
    ---------
    data : list
        A list of dictionaries that the desired value is to be
        extracted from.
    query : str
        The key of the desired value to be extracted from the data set.
    reject_statement : list OR str OR int OR float OR bool
        A value that is used to identify what is classed as a blank
        element.

    Returns
    -------
    return_value : list OR str OR int OR float OR bool
        The value that has been extracted from the inputted data set.

    See Also
    --------
    find_first_value : Finds the first non-blank value in a list.
    create_list_from_dict : Creates a list of a certain element in a
        list of dictionaries.

    Examples
    --------
    >>> l = [{"name": "John", "age": ''}, {"name": "Mike", "age": 35}]
    >>> value = attempt(l, "age", '')
    >>> value
    >>> 35
    """
    try:
        l = create_list_from_dict(data, query)
        return_value = data[find_first_value(l, reject_statement)][query]
    except:
        return_value = "No Data"
    return(return_value)
