import os
import tempfile
import unittest

import objects


class TestObjects(unittest.TestCase):
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.makedirs(os.path.join(self.test_dir, ".vcs", "objects"))
        open(os.path.join(self.test_dir, ".vcs", "index"), "w").close()
        open(os.path.join(self.test_dir, ".vcs", "head"), "w").close()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Возвращает рабочую директорию после выполнения теста."""
        os.chdir(self.original_dir)

    def test_blob_nonexistent_returns_none(self):
        """Проверяет, что create_blob возвращает None для несуществующего файла."""
        self.assertIsNone(objects.create_blob("ghost.txt"))

    def test_blob_returns_hash(self):
        """Проверяет, что create_blob возвращает SHA-1 хеш длиной 40 символов."""
        with open(os.path.join(self.test_dir, "a.txt"), "w") as f:
            f.write("hello")
        self.assertEqual(len(objects.create_blob("a.txt")), 40)

    def test_blob_saves_to_objects(self):
        """Проверяет, что blob-файл сохраняется в .vcs/objects."""
        with open(os.path.join(self.test_dir, "b.txt"), "w") as f:
            f.write("data")
        h = objects.create_blob("b.txt")
        self.assertIn(h, os.listdir(os.path.join(self.test_dir, ".vcs", "objects")))

    def test_create_tree_empty_index(self):
        """Проверяет, что create_tree возвращает None при пустом index."""
        self.assertIsNone(objects.create_tree())

    def test_build_tree_empty(self):
        """Проверяет, что build_tree_structure возвращает пустую структуру для пустого списка."""
        self.assertEqual(objects.build_tree_structure([]), {})

    def test_build_tree_flat(self):
        """Проверяет построение простого дерева для одного файла."""
        tree = objects.build_tree_structure([("100644", "a.txt")])
        self.assertEqual(tree["a.txt"][0], "blob")

    def test_create_tree_with_file(self):
        """Проверяет создание tree-объекта при наличии файла в index."""
        with open(os.path.join(self.test_dir, "f.txt"), "w") as f:
            f.write("hi")
        with open(os.path.join(self.test_dir, ".vcs", "index"), "w") as idx:
            idx.write("100644\tf.txt\n")
        h = objects.create_tree()
        self.assertIsNotNone(h)
        self.assertEqual(len(h), 40)