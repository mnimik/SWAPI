import os
from datetime import datetime
import requests
import petl
from django.core.cache import cache
from .models import StarWarsMeta as SwapiMeta


curr_path = os.path.dirname(__file__)
CSV_DIR = f'{curr_path}/csv/'
API_LINK = 'https://swapi.dev/api/people/'
HTML_TABLE_FILE = 'swapi/templates/dynamic_html/sw_table.html'
STEP_PAGINATION = 10


def validate_result(result):
    '''
    Here should be much more better validation
    :param result:
    :return:
    '''
    assert 'results' in result, 'Invalid data'
    assert 'count' in result, 'Invalid data'
    return result


def add_metadata(meta):
    SwapiMeta(csv_name=meta['name'], record_count=meta['count']).save()


def get_validate_info_from_swapi(link):
    result = requests.get(link).json()
    validate_result(result)

    return result


def fetch_latest_data():
    character_info = list()
    link = API_LINK
    record_count = 0
    while True:
        try:
            result = get_validate_info_from_swapi(link)
            character_info.extend(result['results'])
            if not record_count:
                record_count = result['count']
            if not result.get('next', None):
                break
            link = result['next']
        except TimeoutError:
            break
    save_data_to_csv(character_info, record_count)


def get_homeworld(homeworld_link):
    country = cache.get(homeworld_link)
    if country:
        return country
    country = requests.get(homeworld_link).json().get('name', 'Unknown')
    cache.set(homeworld_link, country, timeout=600)
    return country


def get_date_value(val):
    '''
    Time format using here is ISO 8601

    :param val:
    :return: transformed date
    '''
    transformed_date = val.split('T')[0]
    return transformed_date


fields_to_transform = {
    'edited': {'key': 'date', 'value': get_date_value},
    'homeworld': {'key': 'homeworld', 'value': get_homeworld},
}
allowed_fields = (
    'name', 'height', 'mass', 'hair_color', 'skin_color', 'eye_color', 'birth_year', 'gender', 'homeworld', 'date'
)


def save_data_to_csv(data, record_count):
    db_meta = dict()
    transformed_data = transform_data(data)
    csv_filename = f'{datetime.now().ctime()}.csv'
    csv_file = CSV_DIR+csv_filename
    db_meta['name'] = csv_filename
    db_meta['count'] = record_count
    petl.tocsv(transformed_data, csv_file)
    add_metadata(db_meta)


def transform_data(data):
    tbl_data = petl.fromdicts(data)
    tbl_data = petl.convert(tbl_data, {k: v['value'] for k, v in fields_to_transform.items()})
    tbl_data = petl.rename(tbl_data, {k: v['key'] for k, v in fields_to_transform.items()})
    tbl_data_allowed = petl.cut(tbl_data, *allowed_fields)

    return tbl_data_allowed


def get_csv_list():
    sw_meta = SwapiMeta.objects.all().order_by('-id')
    files = os.listdir(CSV_DIR)
    csv_list = list()
    for record in sw_meta:
        if record.csv_name in files:
            csv_list.append(record)
    return csv_list


def get_html_data(csv_data):
    petl.tohtml(csv_data, HTML_TABLE_FILE)
    with open(HTML_TABLE_FILE, 'r') as f:
        html_data = f.read()
    return html_data


def get_html_data_from_csv(csv_name):
    # get csv file, check if exists
    csv_file = f'{CSV_DIR}/{csv_name}'
    if not os.path.isfile(csv_file):
        return 'No data found'

    # get data from csv file
    csv_data = petl.fromcsv(csv_file)
    # get page num from django cache, default = 1
    page = cache.get(csv_name, 1)
    # cut records
    cut_csv_data = csv_data[:page*STEP_PAGINATION+1]

    # convert csv data to html format by petl
    html_data = get_html_data(cut_csv_data)

    return html_data


def check_need_button(page, count):
    if count > page * STEP_PAGINATION:
        return True
    return False


def increment_page_counter(csv_name):
    page = cache.get(csv_name, 1)
    # check records count to destroy button
    sw_meta = SwapiMeta.objects.get(csv_name=csv_name)
    if not sw_meta:
        return False
    if check_need_button(page, sw_meta.record_count):
        page += 1
        cache.set(csv_name, page, timeout=None)
        return check_need_button(page, sw_meta.record_count)
    return False


def get_counter_table(fields, csv_name):
    if not fields:
        return 'No data to count'
    csv_file = f'{CSV_DIR}/{csv_name}'
    csv_data = petl.fromcsv(csv_file)
    cut_csv_data = petl.cutout(petl.valuecounts(csv_data, *fields), 'frequency')
    html_data = get_html_data(cut_csv_data)
    return html_data
