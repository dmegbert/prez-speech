from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from statistics import median

import textstat
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob

from .utils import safe_cursor


def get_speech_stats(speech_id):
    with safe_cursor() as cur:
        cur.execute('SELECT id, president_id, transcript FROM speeches WHERE id = %s', (speech_id,))
        raw_speech = cur.fetchone()
    speech = {'speech_id': raw_speech.id, 'president_id': raw_speech.president_id, 'speech': raw_speech.transcript}
    raw_text = speech['speech']
    sp_blob = TextBlob(raw_text)
    speech['polarity'], speech['subjectivity'] = sp_blob.sentiment
    speech['word_count'] = len(sp_blob.words)
    speech['sentence_count'] = len(sp_blob.sentences)
    speech['median_sentence_length'] = median([len(sentence) for sentence in sp_blob.sentences])
    common_words = get_top_n_words([raw_text], 50, (1, 1))
    speech['top_50_words'] = json.dumps(common_words)
    speech['grade_reading_level'] = textstat.coleman_liau_index(raw_text)
    return speech


def get_speeches():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_speech_stats, speech_id) for speech_id in range(1, 1022)]
        for future in as_completed(futures):
            try:
                load_speech_stats(future.result())
            except Exception as exc:
                print(exc)


def load_speech_stats(stats, ngrams):
    with safe_cursor() as cur:
        cur.execute(
            'INSERT INTO speech_stats'
            '(speech_id, polarity, subjectivity, word_count,'
            'sentence_count, top_50_words, president_id, grade_reading_level) '
            'VALUES (%(speech_id)s, %(polarity)s, %(subjectivity)s,'
            '%(word_count)s, %(sentence_count)s, %(top_50_words)s, %(president_id)s, %(grade_reading_level)s)',
            stats
        )


def get_top_n_words(corpus, n=20, ngram_range=(1, 1)):
    vec = CountVectorizer(strip_accents='unicode', stop_words='english', ngram_range=ngram_range).fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, int(sum_words[0, idx])) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]
