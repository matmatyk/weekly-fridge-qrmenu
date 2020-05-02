#!/usr/bin/env python3
"""Module docstring"""
import sys
import json
import datetime
import calendar
import locale
from urllib.parse import urlparse
import urllib.request
import qrcode
from bs4 import BeautifulSoup

locale.setlocale(locale.LC_ALL, 'pl_PL.utf8')
START_DATE_KEY = "start_date"
MENU_KEY = "menu"
OTHERS_KEY = "others"
OUTPUT_DIR = "ouptut"


def read_menu(path):
    """Empty docstring """
    with open(path, 'r') as menu_file:
        menu_data = json.load(menu_file)
        return (menu_data[START_DATE_KEY],
                menu_data[MENU_KEY],
                menu_data[OTHERS_KEY])


def uri_validator(url_candidate):
    """Empty docstring """
    try:
        result = urlparse(url_candidate)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        return False


def extract_valid_urls(data):
    """Empty docstring """
    links = []
    for url_candidate in data:
        if not uri_validator(url_candidate):
            continue
        links.append(url_candidate)
    return links


def get_title_for_url(page_url):
    """Empty docstring """
    soup = BeautifulSoup(urllib.request.urlopen(page_url), features="lxml")
    split_title = soup.title.string.split("|")
    return split_title[0].replace("przepis Olga Smile", "").strip()


def date_from_string(start_date_str):
    """Empty docstring """
    try:
        return datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        print("start_date in wrong format. Supported format is YYYY-MM-DD")
        return None


def find_first_monday(start_date_str):
    """Empty docstring """
    start_date = date_from_string(start_date_str)
    MONDAY = 0
    while start_date.weekday() != MONDAY:
        start_date = start_date - datetime.timedelta(days=1)
    return start_date


def print_menu(start_date_str, menu_to_print, other_recipes):
    """Empty docstring """
    current_day = find_first_monday(start_date_str)
    result_str = """
<head>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <table>
        <tr>
"""
    for day_abbr in calendar.day_abbr:
        result_str += "<th>" + day_abbr + "</th>"

    result_str += """
        </tr>
"""
    # printing weeks menu
    cnt = 0
    while True:
        if cnt % 7 == 0:
            if not menu_to_print:
                break
            result_str += """
        <tr>
            <td colspan="7">
            <h2>Tydzień """ + current_day.isoformat() + " --- " + \
                (current_day + datetime.timedelta(days=6)).isoformat() + """</h2>
            </td>
        </tr>
"""
        entry_desc = ""
        entry_qr = None
        if current_day in menu_to_print:
            entry_desc = menu_to_print[current_day]["title"]
            entry_qr = menu_to_print[current_day]["img"]
            menu_to_print.pop(current_day, None)
        result_str += "<td>" + entry_desc + "</br>"
        if entry_qr:
            result_str += "<img src=\"" + entry_qr + \
                          "\" alt=\"" + entry_desc + "\">"
        result_str += "</td>"

        current_day = current_day + datetime.timedelta(days=1)
        cnt = cnt + 1

    # print other recipes
    cnt = 0
    while True:
        if cnt % 7 == 0:
            if cnt >= len(other_recipes):
                break
            if other_recipes and cnt == 0:
                result_str += """
        <tr>
            <td colspan="7">
            <h2>Inne</h2>
            </td>
        </tr>
"""
        entry_desc = ""
        entry_qr = None
        if cnt < len(other_recipes):
            entry_desc = other_recipes[cnt]["title"]
            entry_qr = other_recipes[cnt]["img"]
        result_str += "<td>" + entry_desc + "</br>"
        if entry_qr:
            result_str += "<img src=\"" + entry_qr + \
                          "\" alt=\"" + entry_desc + "\">"
        result_str += "</td>"

        cnt = cnt + 1

    # footer
    result_str += """
    </table>
</body>"""
    return result_str


def do_processing(path):
    """Empty docstring """
    (start_date, menu, others) = read_menu(path)
    url_to_metadata = {}
    for url in extract_valid_urls(menu):
        title = get_title_for_url(url)
        img_path = "images/" + \
                   start_date + "-" + title.replace(" ", "-") + ".png"
        qrcode.make(url).save(img_path)
        url_to_metadata[url] = {
            "title": title,
            "img": img_path
        }

    others_to_print = []
    for url in extract_valid_urls(others):
        title = get_title_for_url(url)
        img_path = "images/" + \
                   start_date + "-" + title.replace(" ", "-") + ".png"
        qrcode.make(url).save(img_path)
        others_to_print.append({
            "title": title,
            "img": img_path
        })

    menu_to_print = {}
    current_day = date_from_string(start_date)
    for entry in menu:
        title = entry
        img = None
        if entry in url_to_metadata:
            title = url_to_metadata[entry]["title"]
            img = url_to_metadata[entry]["img"]
        menu_to_print[current_day] = {
            "title": title,
            "img": img
        }
        current_day = current_day + datetime.timedelta(days=1)

    with open('menu_'+start_date + '.html', 'w') as result_file:
        result_file.write(print_menu(start_date,
                                     menu_to_print,
                                     others_to_print))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Execution: {} path/to/menu.json".format(sys.argv[0]))
        sys.exit(1)
    do_processing(sys.argv[1])
