from django.shortcuts import render, redirect
from .transforms import (
    fetch_latest_data, get_html_data_from_csv, get_csv_list, get_counter_table, allowed_fields, increment_page_counter,
)


def index(request):
    data = get_csv_list()
    params_dict = {'title': 'Star Wars Explorer', 'data': data, 'url': 'info', 'action': 'fetch'}

    return render(request, 'swapi/index.html', params_dict)


def get_swapi(request):
    fetch_latest_data()
    return redirect('index')


def get_info(request, csv_name):
    # if all records have been displayed, we don't need load button on page anymore
    need_button = True
    if request.method == 'POST':
        need_button = increment_page_counter(csv_name)
    data = get_html_data_from_csv(csv_name)
    fields = allowed_fields
    params_dict = {'title': 'Info', 'data': data, 'action': '', 'need_button': need_button, 'fields': fields}
    return render(request, 'swapi/info.html', params_dict)


def counter_table(request):
    fields_to_count = list()
    for param in request.GET.keys():
        if param in allowed_fields:
            fields_to_count.append(param)
    html_table = get_counter_table(fields_to_count, get_csv_list()[0])
    params_dict = {'title': 'Table counter', 'data': html_table}
    return render(request, 'swapi/counter_table.html', params_dict)
