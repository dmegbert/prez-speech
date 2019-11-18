from src.etl.load_president import insert_presidents, read_speeches


def test_db_select():
    insert_presidents()


def test_read_speech():
    read_speeches()