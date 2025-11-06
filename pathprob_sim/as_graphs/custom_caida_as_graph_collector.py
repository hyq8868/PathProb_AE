from datetime import datetime
from functools import cached_property

from bgpy.as_graphs.caida_as_graph.caida_as_graph_collector import CAIDAASGraphCollector
from bgpy.shared.exceptions import NoCAIDAURLError


class CustomCAIDAASGraphCollector(CAIDAASGraphCollector):
    @cached_property
    def default_dl_time(self) -> datetime:
        return datetime(2025, 6, 1, 0, 0, 0)

    def _get_url(self, dl_time: datetime) -> str:
        prepend: str = (
            "https://publicdata.caida.org/datasets/as-relationships/serial-1/"
        )
        urls = [
            prepend + x
            for x in self._get_hrefs(prepend)
            if dl_time.strftime("%Y%m01") in x and "as-rel.txt.bz2" in x
        ]
        print(f"urls: {urls}")
        if len(urls) > 0:
            return str(urls[0])
        else:  # pragma: no cover
            raise NoCAIDAURLError("No Urls")
