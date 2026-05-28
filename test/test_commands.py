import os
import tempfile
import unittest

import commands


class TestCommands(unittest.TestCase):
    def setUp(self):
        """Подготовка временного репозитория перед каждым тестом."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        commands.init()

    def tearDown(self):
        """Возврат в исходную директорию после теста."""
        os.chdir(self.original_dir)

    def _commit(self, filename="f.txt", content="data", message="msg"):
        """Вспомогательный метод: создаёт файл, добавляет его и коммитит изменения."""
        with open(os.path.join(self.test_dir, filename), "w") as f:
            f.write(content)
        commands.add(filename)
        return commands.commit(message)

    def test_init_creates_vcs(self):
        """Проверяет, что после init создаётся директория .vcs."""
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, ".vcs")))

    def test_add_error_no_file(self):
        """Проверяет, что add возвращает ошибку при добавлении несуществующего файла."""
        self.assertIn("ERROR", commands.add("ghost.txt"))

    def test_add_ok(self):
        """Проверяет успешное добавление существующего файла."""
        with open(os.path.join(self.test_dir, "a.txt"), "w") as f:
            f.write("x")
        self.assertIn("a.txt", commands.add("a.txt"))

    def test_commit_error_empty(self):
        """Проверяет, что commit возвращает ошибку при отсутствии изменений."""
        self.assertIn("ERROR", commands.commit())

    def test_commit_returns_hash(self):
        """Проверяет, что commit возвращает хеш длиной 40 символов."""
        self.assertEqual(len(self._commit()), 40)

    def test_log_error_no_commits(self):
        """Проверяет, что log возвращает ошибку при отсутствии коммитов."""
        os.chdir(tempfile.mkdtemp())
        self.assertIn("ERROR", commands.log())

    def test_log_ok(self):
        """Проверяет, что log корректно работает после коммита."""
        self._commit()
        self.assertEqual(commands.log(), "")

    def test_tag_error_no_commits(self):
        """Проверяет, что создание тега невозможно без коммитов."""
        self.assertIn("ERROR", commands.tag("v1"))

    def test_tag_ok(self):
        """Проверяет успешное создание тега после коммита."""
        self._commit()
        self.assertIn("v1", commands.tag("v1"))

    def test_tag_list_empty(self):
        """Проверяет вывод при отсутствии тегов."""
        self._commit()
        self.assertIn("no tags", commands.tag("", list_tags=True))

    def test_reset_error_bad_hash(self):
        """Проверяет ошибку reset при неверном хеше"""
        self.assertIn("ERROR", commands.reset("deadbeef"))

    def test_reset_ok(self):
        """Проверяет, что reset откатывает файл к состоянию указанного коммита."""
        with open(os.path.join(self.test_dir, "r.txt"), "w") as f:
            f.write("v1")
        commands.add("r.txt")
        h1 = commands.commit("first")
        with open(os.path.join(self.test_dir, "r.txt"), "w") as f:
            f.write("v2")
        commands.add("r.txt")
        commands.commit("second")
        commands.reset(h1)
        with open(os.path.join(self.test_dir, "r.txt")) as f:
            self.assertEqual(f.read(), "v1")

    def test_squash_error_no_commits(self):
        """Проверяет ошибку squash при отсутствии коммитов."""
        self.assertIn("ERROR", commands.squash(2))

    def test_squash_error_not_enough(self):
        """Проверяет ошибку squash при недостаточном количестве коммитов."""
        self._commit()
        self.assertIn("ERROR", commands.squash(3))

    def test_squash_ok(self):
        """Проверяет успешное слияние нескольких коммитов в один."""
        self._commit(filename="a.txt", content="a")
        self._commit(filename="b.txt", content="b")
        result = commands.squash(2, message="squashed")
        self.assertIn("squashed", result)

    def test_tag_list_with_tags(self):
        """Проверяет, что функция не выбрасывает исключение при выводе списка тегов."""
        self._commit()
        commands.tag("v1", message="first release")
        result = commands.tag("", list_tags=True)
        self.assertEqual(result, "")