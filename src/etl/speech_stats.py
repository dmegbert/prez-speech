from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import median

from psycopg2.extras import execute_values
import textstat
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob

from src.db_utils import safe_cursor


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
    unigrams_dict = _format_unigrams(common_words, speech['president_id'], speech['speech_id'])
    speech['grade_reading_level'] = textstat.coleman_liau_index(raw_text)
    return speech, unigrams_dict


def _format_unigrams(common_words, president_id, speech_id):
    speech_constants = {'president_id': president_id, 'speech_id': speech_id}
    return [{'unigram': word, 'count': ct, **speech_constants} for word, ct in common_words]


def get_speeches():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_speech_stats, speech_id) for speech_id in range(1, 1022)]
        for future in as_completed(futures):
            try:
                load_speech_stats(future.result())
            except Exception as exc:
                print(exc)


def load_speech_stats(stats_and_unigrams):
    stats, unigrams = stats_and_unigrams
    with safe_cursor() as cur_2:
        execute_values(
            cur_2,
            'INSERT INTO unigrams'
            '(president_id, speech_id, unigram, occurrence)'
            'VALUES %s',
            unigrams,
            '(%(president_id)s, %(speech_id)s, %(unigram)s, %(count)s)'
        )
    with safe_cursor() as cur:
        cur.execute(
            'INSERT INTO speech_stats'
            '(speech_id, polarity, subjectivity, word_count,'
            'sentence_count, president_id, grade_reading_level) '
            'VALUES (%(speech_id)s, %(polarity)s, %(subjectivity)s,'
            '%(word_count)s, %(sentence_count)s, %(president_id)s, %(grade_reading_level)s)',
            stats
        )




def get_top_n_words(corpus, n=20, ngram_range=(1, 1)):
    vec = CountVectorizer(strip_accents='unicode', stop_words='english', ngram_range=ngram_range).fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, int(sum_words[0, idx])) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]
