import unittest
from fzfaws.s3.helper.exclude_file import exclude_file


class TestS3ExcludeFile(unittest.TestCase):
    def test_exclude_file_exclude(self):
        result = exclude_file([".git/*"], [], ".git/COMMIT_EDITMSG")
        self.assertEqual(result, True)

        result = exclude_file([".git/*"], [], "gitconfig.json")
        self.assertEqual(result, False)

    def test_exclude_file_include(self):
        result = exclude_file([], [".git/*"], ".git/COMMIT_EDITMSG")
        self.assertEqual(result, False)

        result = exclude_file([], [".git/*"], "hello.txt")
        self.assertEqual(result, False)

    def test_exclude_file(self):
        result = exclude_file(["*"], ["src/*"], "src/hello.txt")
        self.assertEqual(result, False)

        result = exclude_file(["*"], ["*"], "src/hello.txt")
        self.assertEqual(result, False)

        result = exclude_file(["*"], [".*"], "src/hello.txt")
        self.assertEqual(result, True)
