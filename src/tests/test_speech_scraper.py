from src.scraper.speech_scraper import get_speech_collection_urls, get_speech_urls_for_president, get_speech, get_all_speeches


def test_get_speech_collection_urls():
    urls = get_speech_collection_urls()
    # Stupid ass Grover Cleveland
    assert len(urls) == 44
    for _, url in urls.items():
        assert 'https://' in url
        assert 'presidential-speeches' in url


def test_get_speech_urls_for_president():
    urls = get_speech_urls_for_president()
    assert False


def test_get_speech():
    get_speech('ae')


def test_get_all_speeches():
    get_all_speeches()
