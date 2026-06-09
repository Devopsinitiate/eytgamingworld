import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseIntegrationService(ABC):
    def __init__(self, provider):
        self.provider = provider
        self.last_request_time = 0
        self.min_interval = 60.0 / max(provider.rate_limit_per_min, 1)

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    @abstractmethod
    def get_tournament(self, identifier):
        ...

    @abstractmethod
    def get_event_standings(self, event_id):
        ...

    @abstractmethod
    def get_event_entrants(self, event_id):
        ...

    @abstractmethod
    def get_event_sets(self, event_id):
        ...
