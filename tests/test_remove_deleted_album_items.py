import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gp_sync import sync
from gp_sync.manifest import GOOGLE_ID_MANIFEST_FILENAME, _load_google_id_manifest


class RemoveDeletedAlbumItemsTests(unittest.TestCase):
    def test_deletes_manifest_mapped_file_missing_from_album(self):
        google_id = "AF1QipDeleted"
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)
            album_dir = output_path / "Vacation"
            album_dir.mkdir()
            local_file = album_dir / "photo.jpg"
            local_file.write_bytes(b"deleted photo")
            manifest_path = album_dir / GOOGLE_ID_MANIFEST_FILENAME
            manifest_path.write_text(
                json.dumps({"google_ids": {google_id: "photo.jpg"}}),
                encoding="utf-8",
            )

            deleted_count = sync._remove_deleted_album_items(
                output_path,
                "Vacation",
                album_google_ids=set(),
            )

            self.assertEqual(deleted_count, 1)
            self.assertFalse(local_file.exists())
            self.assertEqual(_load_google_id_manifest(album_dir), {})

    def test_keeps_manifest_mapped_file_still_in_album(self):
        google_id = "AF1QipKept"
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)
            album_dir = output_path / "Vacation"
            album_dir.mkdir()
            local_file = album_dir / "photo.jpg"
            local_file.write_bytes(b"kept photo")
            manifest_path = album_dir / GOOGLE_ID_MANIFEST_FILENAME
            manifest_path.write_text(
                json.dumps({"google_ids": {google_id: "photo.jpg"}}),
                encoding="utf-8",
            )

            deleted_count = sync._remove_deleted_album_items(
                output_path,
                "Vacation",
                album_google_ids={google_id.casefold()},
            )

            self.assertEqual(deleted_count, 0)
            self.assertTrue(local_file.exists())
            self.assertEqual(
                _load_google_id_manifest(album_dir),
                {google_id: "photo.jpg"},
            )

    def test_prunes_stale_manifest_entry_when_file_already_gone(self):
        google_id = "AF1QipStale"
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)
            album_dir = output_path / "Vacation"
            album_dir.mkdir()
            manifest_path = album_dir / GOOGLE_ID_MANIFEST_FILENAME
            manifest_path.write_text(
                json.dumps({"google_ids": {google_id: "missing.jpg"}}),
                encoding="utf-8",
            )

            deleted_count = sync._remove_deleted_album_items(
                output_path,
                "Vacation",
                album_google_ids=set(),
            )

            self.assertEqual(deleted_count, 0)
            self.assertEqual(_load_google_id_manifest(album_dir), {})


class KeepDeletedFlagTests(unittest.TestCase):
    def _run_sync_with_album_items(self, keep_deleted: bool):
        album_title = "Album"
        album_items = [
            {
                "google_id": "AF1QipPresent",
                "url": "https://photos.google.com/photo/AF1QipPresent",
                "identifiers": "present.jpg",
            }
        ]
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(output_dir)
            temp_dir_path = Path(temp_dir)
            album_dir = output_path / album_title
            album_dir.mkdir()
            (album_dir / GOOGLE_ID_MANIFEST_FILENAME).write_text("{}", encoding="utf-8")

            with (
                patch.object(sync, "_collect_album_photo_items", return_value=album_items),
                patch.object(sync, "_album_output_dirs", return_value=[album_dir]),
                patch.object(sync, "_ensure_album_manifest_mappings"),
                patch.object(sync, "_local_album_google_id_files", return_value=({}, [album_dir])),
                patch.object(sync, "_remove_deleted_album_items", return_value=1) as remove_mock,
                patch.object(sync, "_rewrite_full_album_manifest"),
                patch.object(sync, "_cleanup_bootstrap_plain_duplicates"),
                patch.object(sync, "_download_individual_album_items", return_value=(1, 0, 0)),
            ):
                sync._download_missing_album_items_by_google_id(
                    driver=object(),
                    album_title=album_title,
                    output_path=output_path,
                    temp_dir_path=temp_dir_path,
                    keep_deleted=keep_deleted,
                )
            return remove_mock

    def test_default_removes_local_files_deleted_from_album(self):
        album_title = "Album"
        album_items = [
            {
                "google_id": "AF1QipPresent",
                "url": "https://photos.google.com/photo/AF1QipPresent",
                "identifiers": "present.jpg",
            }
        ]
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(output_dir)
            temp_dir_path = Path(temp_dir)
            album_dir = output_path / album_title
            album_dir.mkdir()
            (album_dir / GOOGLE_ID_MANIFEST_FILENAME).write_text("{}", encoding="utf-8")

            with (
                patch.object(sync, "_collect_album_photo_items", return_value=album_items),
                patch.object(sync, "_album_output_dirs", return_value=[album_dir]),
                patch.object(sync, "_ensure_album_manifest_mappings"),
                patch.object(sync, "_local_album_google_id_files", return_value=({}, [album_dir])),
                patch.object(sync, "_remove_deleted_album_items", return_value=1) as remove_mock,
                patch.object(sync, "_rewrite_full_album_manifest"),
                patch.object(sync, "_cleanup_bootstrap_plain_duplicates"),
                patch.object(sync, "_download_individual_album_items", return_value=(1, 0, 0)),
            ):
                sync._download_missing_album_items_by_google_id(
                    driver=object(),
                    album_title=album_title,
                    output_path=output_path,
                    temp_dir_path=temp_dir_path,
                )
            remove_mock.assert_called_once()

    def test_keep_deleted_skips_local_file_removal(self):
        remove_mock = self._run_sync_with_album_items(keep_deleted=True)
        remove_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
