# -*- coding: utf-8 -*-

import glob
import json
import os
import re
import sqlite3
import sys
from typing import Dict, Iterable, Union

from resworb.base import (
    BookmarkMixin,
    CloudTabMixin,
    HistoryMixin,
    OpenedTabMixin,
    ReadingMixin,
    URLItem,
)
from resworb.exporter import ExportMixin


class FirefoxOpenedTabs(OpenedTabMixin):
    session_file: str

    def get_opened_tabs(self) -> Iterable[URLItem]:
        # References:
        # https://gist.github.com/tmonjalo/33c4402b0d35f1233020bf427b5539fa
        # pylint: disable=import-outside-toplevel
        import lz4.block

        with open(self.session_file, mode="rb") as f:
            bytes_ = f.read()
            if bytes_[:8] == b"mozLz40\0":
                bytes_ = lz4.block.decompress(bytes_[8:])
                data = json.loads(bytes_)

                for window in data["windows"]:
                    for tab in window["tabs"]:
                        i = tab["index"] - 1
                        yield {
                            "title": tab["entries"][i]["title"],
                            "url": tab["entries"][i]["url"],
                        }


class FirefoxCloudTabs(CloudTabMixin):
    def get_cloud_tabs(self) -> Iterable[URLItem]:
        raise NotImplementedError


class FirefoxReadings(ReadingMixin):
    def get_readings(self) -> Iterable[URLItem]:
        raise NotImplementedError


class FirefoxBookmarks(BookmarkMixin):
    history_file: str

    def _get_bookmarks_folders(self):
        with sqlite3.connect(self.history_file) as conn:
            sql = """
            SELECT id, type, parent, title
            FROM moz_bookmarks
            WHERE type=2;
            """
            columns = ["id", "type", "parent", "title"]

            return [dict(zip(columns, r)) for r in conn.cursor().execute(sql)]

    def get_bookmarks(self, flatten: bool = True) -> Union[Iterable[URLItem], Dict]:
        bookmark_folders = self._get_bookmarks_folders()
        bookmark_folders = {x["id"]: x for x in bookmark_folders}

        def _get_bookmark_folders(parent):
            folders = []
            folder = bookmark_folders[parent]
            while folder["parent"] > 0:
                folders += [folder["title"]]
                folder = bookmark_folders[folder["parent"]]

            return list(reversed(folders))

        with sqlite3.connect(self.history_file) as conn:
            sql = """
            SELECT type, parent, moz_bookmarks.title, moz_places.url
            FROM moz_bookmarks
            INNER JOIN moz_places on moz_bookmarks.fk=moz_places.id
            WHERE type=1
            ORDER BY dateAdded desc;
            """

            for _, parent, title, url in conn.cursor().execute(sql):
                yield {
                    "title": title,
                    "url": url,
                    "folders": _get_bookmark_folders(parent),
                }


class FirefoxHistories(HistoryMixin):
    def get_histories(self) -> Iterable[Dict]:
        with sqlite3.connect(self.history_file) as conn:
            sql = """
            SELECT place_id, url, title, datetime((visit_date/1000000), 'unixepoch', 'localtime') AS visit_date
            FROM moz_places INNER JOIN moz_historyvisits on moz_historyvisits.place_id = moz_places.id
            ORDER BY visit_date DESC
            """

            for id_, url, title, visit_time in conn.cursor().execute(sql):
                yield {
                    "id": id_,
                    "url": url,
                    "title": title,
                    "visit_time": visit_time,
                }


def get_default_library_path() -> str:
    platform = sys.platform
    if re.match("win.*", platform):
        return os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            "Mozilla",
            "Firefox",
            "Profiles",
        )

    if re.match("darwin", platform):
        return os.path.join(
            os.environ["HOME"],
            "Library",
            "Application Support",
            "Firefox",
        )

    raise RuntimeError(f"Unsupported platform: {platform}")


class Firefox(
    ExportMixin,
    FirefoxOpenedTabs,
    FirefoxCloudTabs,
    FirefoxReadings,
    FirefoxBookmarks,
    FirefoxHistories,
):  # pylint: disable=too-many-ancestors
    def __init__(self, library: str = get_default_library_path()) -> None:
        super().__init__()

        self.library = library

        session_files = glob.glob(
            os.path.join(
                self.library,
                "*.default*",
                "sessionstore-backups",
                "recovery.jsonlz4",
            ),
            recursive=True,
        )
        if not session_files:
            raise RuntimeError(f"Session file not found in {self.library}")
        self.session_file = session_files[0]

        history_files = glob.glob(
            os.path.join(self.library, "*.default*", "places.sqlite"),
            recursive=True,
        )
        if not history_files:
            raise RuntimeError(f"History file not found in {self.library}")
        self.history_file = history_files[0]
