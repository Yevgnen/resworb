# -*- coding: utf-8 -*-

import abc
import json
import pickle
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

import pytoml
import yaml

from resworb.base import URLItem


class ExportMixin(object):
    def _deduplicate(self, items: Iterable[URLItem]) -> Iterable[URLItem]:
        processed = set()
        for x in items:
            if x["url"] not in processed:
                processed.add(x["url"])
                yield x

    def export(
        self, kinds: Union[str, Iterable[str]] = "all", drop_duplicates: bool = True
    ) -> Dict[str, List]:
        def _wrapper(f):
            if drop_duplicates:
                return self._deduplicate(f())

            return f()

        factory = {
            "opened_tabs": self.get_opened_tabs,
            "cloud_tabs": self.get_cloud_tabs,
            "readings": self.get_readings,
            "bookmarks": self.get_bookmarks,
            "histories": self.get_histories,
        }
        if kinds == "all":
            return {k: list(_wrapper(v)) for k, v in factory.items()}

        if isinstance(kinds, str):
            kinds = [kinds]

        return {kind: list(_wrapper(factory[kind])) for kind in kinds}


class Exporter(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def export_to_file(
        self,
        data: Any,
        filename: str,
        file_kwargs: Optional[Mapping] = None,
        dump_kwargs: Optional[Mapping] = None,
    ) -> None:
        raise NotImplementedError()


class YAMLExporter(Exporter):
    def export_to_file(
        self,
        data: Any,
        filename: str,
        file_kwargs: Optional[Mapping] = None,
        dump_kwargs: Optional[Mapping] = None,
    ) -> None:
        if not file_kwargs:
            file_kwargs = {"mode": "w"}

        if not dump_kwargs:
            dump_kwargs = {
                "allow_unicode": True,
                "explicit_start": True,
                "indent": 2,
            }

        with open(filename, **file_kwargs) as f:
            yaml.safe_dump(data, f, **dump_kwargs)


class TOMLExporter(Exporter):
    def export_to_file(
        self,
        data: Any,
        filename: str,
        file_kwargs: Optional[Mapping] = None,
        dump_kwargs: Optional[Mapping] = None,
    ) -> None:
        if not file_kwargs:
            file_kwargs = {"mode": "w"}

        if not dump_kwargs:
            dump_kwargs = {}

        with open(filename, **file_kwargs) as f:
            pytoml.dump(data, f, **dump_kwargs)


class JSONExporter(Exporter):
    def export_to_file(
        self,
        data: Any,
        filename: str,
        file_kwargs: Optional[Mapping] = None,
        dump_kwargs: Optional[Mapping] = None,
    ) -> None:
        if not file_kwargs:
            file_kwargs = {"mode": "w"}

        if not dump_kwargs:
            dump_kwargs = {
                "ensure_ascii": False,
                "indent": 4,
            }

        with open(filename, **file_kwargs) as f:
            json.dump(data, f, **dump_kwargs)


class PickleExporter(Exporter):
    def export_to_file(
        self,
        data: Any,
        filename: str,
        file_kwargs: Optional[Mapping] = None,
        dump_kwargs: Optional[Mapping] = None,
    ) -> None:
        if not file_kwargs:
            file_kwargs = {"mode": "wb"}

        if not dump_kwargs:
            dump_kwargs = {}

        with open(filename, **file_kwargs) as f:
            pickle.dump(data, f, **dump_kwargs)
