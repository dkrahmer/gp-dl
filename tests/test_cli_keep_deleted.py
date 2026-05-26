import unittest

from gp_sync import cli


class CliKeepDeletedTests(unittest.TestCase):
    def test_keep_deleted_flag_is_accepted(self):
        args = cli.parse_cli_args(
            [
                "--album-urls",
                "https://example.com/album",
                "--output-dir",
                "out",
                "--keep-deleted",
            ]
        )
        self.assertTrue(args.keep_deleted)


if __name__ == "__main__":
    unittest.main()
