import os
import main
import unittest
import tempfile

PATH_DATABASE = "data/db.sqlite"


class TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, PATH_DATABASE = tempfile.mkstemp()
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()
        main.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(PATH_DATABASE)

    # test cases for post_new_game(len=3)
    def test_create_game_with_len_1(self):
        rv = self.app.post('/game/new/?game_size=1')
        assert 'Defined game size too small' in rv.data

    def test_create_game_with_len_7(self):
        rv = self.app.post('/game/new/?game_size=7')
        assert 'game_id' in rv.data

    # test cases for get_existing_games()
    def test_get_all_status(self):
        rv = self.app.get('/game/lists/all')
        assert 'Successfully retrieved' or 'No existing games' in rv.data

    def test_get_status_with_id_1(self):
        self.app.post('/game/new/?game_size=3')
        rv = self.app.get('/game/lists/?game_id=1')
        assert 'Successfully retrieved' in rv.data

    def test_get_status_with_id_10(self):
        rv = self.app.get('/game/lists/?game_id=10')
        assert 'Game with id' in rv.data

    # test cases for put_move(id=None, row=None, col=None, mark=None)
    def test_put_move_with_id_10(self):
        rv = self.app.post('/game/move/?game_id=10&row=1&col=1&mark=1')
        assert 'Game with id' in rv.data

    def test_put_move_with_row_4(self):
        self.app.post('/game/new/?game_size=3')
        rv = self.app.post('/game/move/?game_id=1&row=4&col=1&mark=1')
        assert 'Unqualified placement' in rv.data

    def test_put_move_with_row_n1(self):
        self.app.post('/game/new/?game_size=3')
        rv = self.app.post('/game/move/?game_id=1&row=-1&col=4&mark=1')
        assert 'Unqualified placement' in rv.data

    def test_put_move_in_id1_row1_col1_marko(self):
        self.app.post('/game/new/?game_size=3')
        rv = self.app.post('/game/move/?game_id=1&row=1&col=1&mark=1')
        assert 'Game continue' in rv.data

    def test_put_move_in_id1_row1_col1_markx(self):
        self.app.post('/game/new/?game_size=3')
        self.app.post('/game/move/?game_id=1&row=1&col=1&mark=1')
        rv = self.app.post('/game/move/?game_id=1&row=1&col=1&mark=0')
        assert 'Position already taken' in rv.data

    def test_winning_case(self):
        self.app.post('/game/new/?game_size=3')
        self.app.post('/game/move/?game_id=1&row=2&col=1&mark=1')
        self.app.post('/game/move/?game_id=1&row=2&col=2&mark=1')
        rv = self.app.post('/game/move/?game_id=1&row=2&col=3&mark=1')
        assert "winner side's mark is" in rv.data

    def test_draw_case(self):
        mark = 1
        self.app.post('/game/new/?game_size=2')
        self.app.post('/game/move/?game_id=1&row=1&col=1&mark=1')
        self.app.post('/game/move/?game_id=1&row=2&col=1&mark=0')
        self.app.post('/game/move/?game_id=1&row=2&col=2&mark=1')
        rv = self.app.post('/game/move/?game_id=1&row=1&col=2&mark=0')
        assert "Game end, draw." in rv.data

    # test cases for delete_game(id=None)
    def test_del_game_with_id_10(self):
        rv = self.app.delete('/game/?game_id=10')
        assert 'Game with id' in rv.data

    def test_del_game_with_id_1(self):
        self.app.post('/game/new/?game_size=3')
        self.app.post('/game/new/?game_size=3')
        self.app.post('/game/new/?game_size=3')
        rv = self.app.delete('/game/?game_id=3')
        assert 'Specified game is deleted' in rv.data

if __name__ == '__main__':
    unittest.main()
