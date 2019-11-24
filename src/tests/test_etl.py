from src.etl.load_president import insert_presidents, read_speeches
from src.etl.speech_stats import get_speeches


# def test_db_select():
#     insert_presidents()
#
#
# def test_read_speech():
#     read_speeches()

def test_get_speeches():
    get_speeches()
