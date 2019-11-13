import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

URL_SUFFIXES = ['washington', 'adams', 'jefferson', 'madison', 'monroe', 'jqadams', 'jackson', 'vanburen', 'harrison',
                'tyler', 'polk', 'taylor', 'fillmore', 'pierce', 'buchanan', 'lincoln', 'johnson', 'grant', 'hayes',
                'garfield', 'arthur', 'cleveland', 'bharrison', 'mckinley', 'roosevelt', 'taft',
                'wilson', 'harding', 'coolidge', 'hoover', 'fdroosevelt', 'truman', 'eisenhower', 'kennedy',
                'lbjohnson',
                'nixon', 'ford', 'carter', 'reagan', 'bush', 'clinton', 'gwbush', 'obama']

MILLER_BASE_URL = 'https://millercenter.org'
PREZ_DETAILS_URL = (MILLER_BASE_URL + '/president/{}').format
SPEECH_URL = (MILLER_BASE_URL + '{}').format
PAGINATION_URL = (MILLER_BASE_URL + '/the-presidency/presidential-speeches{}').format


def get_speech_collection_urls():
    speech_urls = {}
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(_get_speech_collection_url, suffix): suffix for suffix in URL_SUFFIXES}
        for future in as_completed(future_to_url):
            suffix = future_to_url[future]
            try:
                speech_urls[suffix] = future.result()
            except Exception as exc:
                print(exc)

    # Eisenhower's doesn't have the beginning of the url b/c why be consistent?
    speech_urls[
        'eisenhower'] = 'https://millercenter.org/the-presidency/presidential-speeches?field_president_target_id%5B0%5D=33&field_president_target_id%5B1%5D=33#selected-tags'
    return speech_urls


def _get_speech_collection_url(suffix):
    resp = requests.get(PREZ_DETAILS_URL(suffix))
    details_page = BeautifulSoup(resp.content, 'html.parser')
    speech_div = details_page.find('div', class_='president-speeches-cta')
    return speech_div.find('a').get('href')


def get_speech_urls_for_president():
    president_to_collection_urls = get_speech_collection_urls()
    president_to_individual_speech_urls = {}
    for prez, collection_url in president_to_collection_urls.items():
        urls = _get_speech_urls(collection_url)
        print(prez)
        president_to_individual_speech_urls[prez] = urls

    with open('/Users/egbert/projects/prez-speech/data/prez-speeches-urls.json', 'w') as file:
        json.dump(president_to_individual_speech_urls, file)


def _handle_scroll_page_to_get_urls(url, speech_urls):
    resp = requests.get(url)
    speeches_page = BeautifulSoup(resp.content, 'html.parser')
    infinite_speech_div = speeches_page.find('div', class_='views-infinite-scroll-content-wrapper')
    suffixes = infinite_speech_div.find_all('a')
    for suffix in suffixes:
        speech_urls.append(SPEECH_URL(suffix.get('href')))
    pager = speeches_page.find('li', class_='pager__item')
    return speech_urls, pager


def _get_speech_urls(collection_url):
    speech_urls = []
    speech_urls, pager = _handle_scroll_page_to_get_urls(collection_url, speech_urls)
    while pager:
        next_page_url = PAGINATION_URL(pager.find('a').get('href'))
        speech_urls, pager = _handle_scroll_page_to_get_urls(next_page_url, speech_urls)
    return speech_urls


def get_all_speeches():
    with open('/Users/egbert/projects/prez-speech/data/prez-speeches-urls.json', 'r') as file:
        prez_to_speech_urls = json.load(file)
    speech_urls = [url for urls in prez_to_speech_urls.values() for url in urls]
    prez_to_speeches = defaultdict(list)
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_speech, speech_url) for speech_url in speech_urls]
        for future in as_completed(futures):
            try:
                speech = future.result()
                print(speech.get('president', 'Missing Prez'))
                prez_to_speeches[speech.get('president', 'Missing Prez')].append(speech)
            except Exception as exc:
                print(f'future failed because: {exc}')

    with open('/Users/egbert/projects/prez-speech/data/prez-speeches-final.json', 'w') as file:
        json.dump(prez_to_speeches, file)


def get_speech(url):
    resp = requests.get(url)
    speech_page = BeautifulSoup(resp.content, 'html.parser')
    transcript_div = speech_page.find('div', class_='view-transcript')
    transcript_paras = transcript_div.find_all('p')
    speech_paragraphs = []
    for para in transcript_paras:
        speech_paragraphs.append(para.text)
    speech = ' '.join(speech_paragraphs)
    speech = speech.replace(u'\xa0', u' ')
    meta = _get_speech_meta(speech_page)
    return {**meta, 'transcript': speech}


def _get_speech_meta(page):
    meta_div = page.find('div', class_='about-this-episode')
    president_name, date, source, description = '', '', '', ''
    try:
        president_name = meta_div.find('p', class_='president-name').text
    except AttributeError:
        pass
    try:
        date = meta_div.find('p', class_='episode-date').text
    except AttributeError:
        pass
    try:
        source = meta_div.find('span', class_='speech-loc').text
    except AttributeError:
        pass
    try:
        description = meta_div.find('p', id='description').text
    except AttributeError:
        pass
    return {'president': president_name, 'date': date, 'source': source, 'description': description}


def main():
    get_all_speeches()


if __name__ == '__main__':
    main()
