from typing import Dict, Iterable, Union

URLItem = Dict[str, str]


class OpenedTabMixin:
    def get_opened_tabs(self) -> Iterable[URLItem]:
        raise NotImplementedError


class CloudTabMixin:
    cloud_tab_file: str

    def get_cloud_tabs(self) -> Iterable[URLItem]:
        raise NotImplementedError


class ReadingMixin:
    def get_readings(self) -> Iterable[URLItem]:
        raise NotImplementedError


class BookmarkMixin:
    bookmark_file: str

    def get_bookmarks(self, flatten: bool = True) -> Union[Iterable[URLItem], Dict]:
        raise NotImplementedError


class HistoryMixin:
    history_file: str

    def get_histories(self) -> Iterable[Dict]:
        raise NotImplementedError
