from app import mongo
import re
import pdb
import string
from flask import flash
import random
from datetime import datetime
import os


def utils_generate_pagination(pageno, maxpage):
    if pageno < 1 or maxpage < 1 or pageno > maxpage:
        # pdb.set_trace()
        raise ValueError('Invalid Input')

    elif maxpage > 6:
        if maxpage - 2 > pageno > 3:
            return [1, None, pageno - 1, pageno, pageno + 1, None, maxpage]
        elif pageno <= 3:
            return list(range(1, max(3, pageno + 2))) + [None, maxpage]
        elif pageno == maxpage - 1:
            return [1, None, pageno - 1, pageno, pageno + 1]
        elif pageno == maxpage - 2:

            return [1, None, pageno - 1, pageno, pageno + 1, maxpage]
        if pageno == maxpage:
            return [1, None, pageno-1, maxpage]
    elif maxpage <= 4:
        return list(range(1, maxpage + 1))
    else:
        # pdb.set_trace()
        raise ValueError('Invalid Input')

def a_random_string_of_length(n):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for i in range(n))

def parse_filesize(bytes):
    if bytes < 10**3:
        return "%sB" % str(bytes)
    elif bytes < 10**6:
        return "%sKB" % str((bytes // 10**2) / 10)
    elif bytes < 10**9:
        return "%sMB" % str((bytes // 10**5) / 10)
    else:
        return "%sGB" % str((bytes // 10**8) / 10)


class KUBOSFormValidator():
    def __init__(self, structure):
        error_msg = '\'structure\' argument must be a dict with form field names (strings) as keys and tuples as values. The tuples contain two items. First is the function to validate the input. This function should return True or False. Next is the error message to flash if the value does not meet pass the validation test.'
        if type(structure) != dict:
            raise TypeError(error_msg)
        for key, value in structure.items():
            if type(key) != str or type(value) != tuple or not hasattr(value[0], '__call__') or len(value) != 2 or type(value[1]) != str:
                raise TypeError(error_msg)

        self.structure = structure

    def validate(self, formdata):
        data = formdata.copy()
        if 'csrf_token' in data:
            del data['csrf_token']

        if self.structure.keys() != data.keys():
            print(self.structure.keys())
            print(data.keys())
            return False

        form_is_valid = True
        for fieldname, fieldvalue in data.items():
            if not self.structure[fieldname][0](fieldvalue):
                form_is_valid = False
                print('flashing')
                flash(self.structure[fieldname][1], 'warning')
        return form_is_valid

kz_validator_str = lambda x: type(x) == str

def kz_validator_plaintext(x):
    symbols = set(string.punctuation)
    return not(any(char.isdigit() for char in x) or any(char in symbols for char in x))

kz_do_not_validate = lambda x: True
kz_validator_digit = lambda x: x.isdigit()
kz_validator_bool = lambda x: type(x) == bool
kz_validator_float = lambda x: type(x) == float


def kz_validator_email(x):
    return re.match(r"[^@]+@[^@]+\.[^@]+", x)


def kz_validator_builder_password(length, characters):
    """Returns a password validator (function) with one argument (string) with a requirement that all passwords must have at least one of each type of character in characters and must be at least 'length' characters long. Character is an array with 'uppercase', 'numbers', 'symbols' as possible values."""

    def validator(text):
        if 'uppercase' in characters:
            if not any(char.isupper() for char in text):
                return False
        if 'numbers' in characters:
            if not any(char.isdigit() for char in text):
                return False
        if 'symbols' in characters:
            symbols = set(string.punctuation)
            if not any(char in symbols for char in text):
                return False
        if len(text) < length:
            return False
        return True

    return validator

def kz_validator_datestr(text):
    if type(text) != str:
        return False
    try:
        print(datetime.strptime(text, '%d-%m-%Y'))
    except Exception as e:
        print('This is an anticipated exception.')
        print(e.args[0])
        return False
    return True

def unique_mongo_id():
    existing_ids = [entry['id'] for entry in mongo.db.page_content.find()] + [entry['id'] for entry in mongo.db.program.find()] + [entry['id'] for entry in mongo.db.news.find()]
    candidate = a_random_string_of_length(10)
    iteration = 0
    while candidate in existing_ids and iteration < 10000:
        candidate = a_random_string_of_length(10)
        iteration += 1
    if candidate in existing_ids:
        raise ValueError('Could not generate unique id after 10,000 iterations. Try again.')
    return candidate

def unique_file_name(length):
    name_list = []
    for root, directories, filenames in os.walk('app/uploads'):
        for filename in filenames:
            name_list.append(filename)
    iterator = 0
    candidate = a_random_string_of_length(length)
    while candidate in name_list and iterator < 10000:
        candidate = a_random_string_of_length(length)
        iterator += 1
    if candidate in name_list:
        raise ValueError('Cannot find uniqe name after 10000 iterations.')
    return candidate

def add_trailing_zeroes(number, string_length):
    str_num = str(number)
    while len(str_num) < string_length:
        str_num = '0' + str_num
    return str_num