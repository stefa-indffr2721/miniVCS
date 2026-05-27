import os
import tempfile
import unittest

import repository


class TestRepository(unittest.TestCase):
    def setUp(self):
        """Создаёт временную директорию-репозиторий для тестов."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Возвращает рабочую директорию после выполнения теста."""
        os.chdir(self.original_dir)

    def test_escape_space(self):
        """Проверяет экранирование пробела в пути."""
        self.assertEqual(repository.escape_path("my file.txt"), "my\\sfile.txt")

    def test_escape_tab(self):
        """Проверяет экранирование табуляции в пути."""
        self.assertEqual(repository.escape_path("my\tfile.txt"), "my\\tfile.txt")

    def test_unescape_space(self):
        """Проверяет обратное преобразование экранированного пробела."""
        self.assertEqual(repository.unescape_path("my\\sfile.txt"), "my file.txt")

    def test_roundtrip(self):
        """Проверяет корректность из escape в unescape."""
        path = "dir\\my file.txt"
        self.assertEqual(repository.unescape_path(repository.escape_path(path)), path)

    def test_check_repo_false(self):
        """Проверяет, что check_repo возвращает False вне репозитория."""
        self.assertFalse(repository.check_repo())

    def test_check_repo_true(self):
        """Проверяет, что check_repo обнаруживает .vcs-репозиторий."""
        os.makedirs(os.path.join(self.test_dir, ".vcs"))
        self.assertTrue(repository.check_repo())

    def test_find_repo_none(self):
        """Проверяет, что find_repo возвращает None, если репозиторий не найден."""
        self.assertIsNone(repository.find_repo())

    def test_find_repo_found(self):
        """Проверяет, что find_repo находит корень репозитория."""
        os.makedirs(os.path.join(self.test_dir, ".vcs"))
        self.assertEqual(os.path.realpath(repository.find_repo()), os.path.realpath(self.test_dir))

    def test_gc_no_repo(self):
        """Проверяет, что gc возвращает ошибку если репозиторий отсутствует."""
        self.assertIn("ERROR", repository.gc())

    def test_gc_empty_repo(self):
        """Проверяет работу gc на пустом репозитории."""
        os.makedirs(os.path.join(self.test_dir, ".vcs", "objects"))
        os.makedirs(os.path.join(self.test_dir, ".vcs", "log"))
        open(os.path.join(self.test_dir, ".vcs", "index"), "w").close()
        open(os.path.join(self.test_dir, ".vcs", "head"), "w").close()
        self.assertIn("GC", repository.gc())

    def test_gc_removes_unreachable(self):
        """Проверяет, что gc удаляет недостижимые объекты."""
        os.makedirs(os.path.join(self.test_dir, ".vcs", "objects"))
        os.makedirs(os.path.join(self.test_dir, ".vcs", "log"))
        open(os.path.join(self.test_dir, ".vcs", "index"), "w").close()
        open(os.path.join(self.test_dir, ".vcs", "head"), "w").close()

        with open(os.path.join(self.test_dir, ".vcs", "objects", "aabbcc"), "w") as f:
            f.write("garbage")
        repository.gc()
        self.assertNotIn("aabbcc", os.listdir(os.path.join(self.test_dir, ".vcs", "objects")))