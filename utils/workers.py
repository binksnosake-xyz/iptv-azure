# utils/workers.py - QThread workers pour les appels API asynchrones
import logging
from PyQt5.QtCore import QThread, pyqtSignal
from utils.api import XtreamClient, M3UParser

logger = logging.getLogger(__name__)


class AuthWorker(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, host, username, password):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password

    def run(self):
        try:
            client = XtreamClient(self.host, self.username, self.password)
            data = client.authenticate()
            self.success.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class LiveStreamsWorker(QThread):
    success = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            categories = self.client.get_live_categories()
            streams = self.client.get_live_streams()
            self.success.emit(categories, streams)
        except Exception as e:
            self.error.emit(str(e))


class VODWorker(QThread):
    success = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            categories = self.client.get_vod_categories()
            streams = self.client.get_vod_streams()
            self.success.emit(categories, streams)
        except Exception as e:
            self.error.emit(str(e))


class SeriesWorker(QThread):
    success = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            categories = self.client.get_series_categories()
            series = self.client.get_series()
            self.success.emit(categories, series)
        except Exception as e:
            self.error.emit(str(e))


class M3UWorker(QThread):
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, source, is_url=False):
        super().__init__()
        self.source = source
        self.is_url = is_url

    def run(self):
        try:
            if self.is_url:
                channels = M3UParser.parse_url(self.source)
            else:
                channels = M3UParser.parse_file(self.source)
            self.success.emit(channels)
        except Exception as e:
            self.error.emit(str(e))
