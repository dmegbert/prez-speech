import csv
from datetime import datetime
import sys

from psycopg2.extras import execute_values
from unidecode import unidecode

from src.db_utils import safe_cursor

csv.field_size_limit(sys.maxsize)

RAW_PRESIDENTS = ['George Washington', 'John Adams', 'Thomas Jefferson', 'James Madison', 'James Monroe',
                  'John Quincy Adams', 'Andrew Jackson', 'Martin Van Buren', 'William H. Harrison', 'John Tyler',
                  'James K. Polk', 'Zachary Taylor', 'Millard Fillmore', 'Franklin Pierce', 'James Buchanan',
                  'Abraham Lincoln', 'Andrew Johnson', 'Ulysses S. Grant', 'Rutherford B. Hayes', 'James A. Garfield',
                  'Chester A. Arthur', 'Grover Cleveland', 'Benjamin Harrison', 'Grover Cleveland', 'William McKinley',
                  'Theodore Roosevelt', 'William H. Taft', 'Woodrow Wilson', 'Warren G. Harding', 'Calvin Coolidge',
                  'Herbert Hoover', 'Franklin D. Roosevelt', 'Harry S. Truman', 'Dwight D. Eisenhower',
                  'John F. Kennedy', 'Lyndon B. Johnson', 'Richard M. Nixon', 'Gerald R. Ford', 'Jimmy Carter',
                  'Ronald Reagan', 'George H. W. Bush', 'Bill Clinton', 'George W. Bush', 'Barack Hussein Obama',
                  'Donald J. Trump']

PREZ_TO_ID = {'George Washington': 1,
              'John Adams': 2,
              'Thomas Jefferson': 3,
              'James Madison': 4,
              'James Monroe': 5,
              'John Quincy Adams': 6,
              'Andrew Jackson': 7,
              'Martin Van Buren': 8,
              'John Tyler': 10,
              'James K. Polk': 11,
              'Zachary Taylor': 12,
              'Millard Fillmore': 13,
              'Franklin Pierce': 14,
              'James Buchanan': 15,
              'Abraham Lincoln': 16,
              'Andrew Johnson': 17,
              'Ulysses S. Grant': 18,
              'Rutherford B. Hayes': 19,
              'James A. Garfield': 20,
              'Chester A. Arthur': 21,
              'Grover Cleveland': 22,
              'Benjamin Harrison': 23,
              'William McKinley': 25,
              'Theodore Roosevelt': 26,
              'Woodrow Wilson': 28,
              'Warren G. Harding': 29,
              'Calvin Coolidge': 30,
              'Herbert Hoover': 31,
              'Franklin D. Roosevelt': 32,
              'Harry S. Truman': 33,
              'Dwight D. Eisenhower': 34,
              'John F. Kennedy': 35,
              'Lyndon B. Johnson': 36,
              'Richard M. Nixon': 37,
              'Jimmy Carter': 39,
              'Ronald Reagan': 40,
              'George H. W. Bush': 41,
              'Bill Clinton': 42,
              'George W. Bush': 43,
              'William Taft': 27,
              'Gerald Ford': 38,
              'William Harrison': 9,
              'Barack Obama': 44,
              'Donald Trump': 45}


def prep_presidents():
    presidents = {idx + 1: name for idx, name in enumerate(RAW_PRESIDENTS)}
    names = [name.split(' ') for name in presidents.values()]
    names[-5:-4] = [['George', 'H. W.', 'Bush']]
    for num, prez in presidents.items():
        idx = num - 1
        if len(names[idx]) == 2:
            names[idx].insert(1, None)
        names[idx].append(prez)
        names[idx] = tuple(names[idx])
    return names


def db_select():
    with safe_cursor() as cur:
        cur.execute('SELECT * FROM test')
        return cur.fetchall()


def insert_presidents():
    data = prep_presidents()
    with safe_cursor() as cur:
        execute_values(
            cur,
            'INSERT INTO presidents (first_name, middle_initial, last_name, display_name) VALUES %s',
            data
        )


blah = ['president', 'date', 'source', 'description', 'transcript']


def prep_speech(speech):
    speech['transcript'] = speech['transcript'].replace('\r\n', ' ')
    speech['transcript'] = speech['transcript'].replace('\n', ' ')
    speech['transcript'] = speech['transcript'].replace('\r', ' ')
    speech['transcript'] = unidecode(speech['transcript'])
    speech['president_id'] = PREZ_TO_ID[speech.pop('president')]
    speech['speech_date'] = datetime.strptime(speech.pop('date'), '%B %d, %Y').date()
    speech.pop('source')
    speech.pop('description')
    return speech


def load_speech(speech):
    with safe_cursor() as cur:
        cur.execute(
            'INSERT INTO speeches '
            '(transcript, president_id, speech_date) '
            'VALUES (%(transcript)s, %(president_id)s, %(speech_date)s)',
            speech
        )


def read_speeches():
    with open('/Users/egbert/projects/prez-speech/data/prez-speeches-final.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for speech in reader:
            clean_speech = prep_speech(speech)
            load_speech(clean_speech)
