import requests
import logging
from .base import BaseIntegrationService

logger = logging.getLogger(__name__)

STARTGG_API_URL = "https://api.start.gg/gql/alpha"


class StartGGService(BaseIntegrationService):
    def __init__(self, provider):
        super().__init__(provider)
        self.api_key = provider.api_key

    def _request(self, query, variables=None):
        self._rate_limit()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(STARTGG_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise Exception(f"start.gg API error: {data['errors']}")
        return data.get("data", {})

    def get_tournament(self, slug):
        query = """
        query TournamentQuery($slug: String!) {
            tournament(slug: $slug) {
                id name slug startAt endAt
                city addrState countryName
                events { id name slug game { id name } }
                standings(query: { perPage: 8 }) { nodes { placement entrant { id name } } }
            }
        }
        """
        return self._request(query, {"slug": slug})

    def get_event_standings(self, event_id):
        query = """
        query EventStandings($eventId: ID!) {
            event(id: $eventId) {
                standings(query: { perPage: 50 }) {
                    nodes { placement entrant { id name } }
                }
            }
        }
        """
        return self._request(query, {"eventId": str(event_id)})

    def get_event_entrants(self, event_id):
        query = """
        query EventEntrants($eventId: ID!) {
            event(id: $eventId) {
                entrants(query: { perPage: 50 }) {
                    nodes { id name }
                }
            }
        }
        """
        return self._request(query, {"eventId": str(event_id)})

    def get_event_sets(self, event_id):
        query = """
        query EventSets($eventId: ID!) {
            event(id: $eventId) {
                sets(page: 1, perPage: 50) {
                    nodes {
                        id round
                        slots { entrant { id name } }
                        displayScore
                        winnerId
                        completedAt
                    }
                }
            }
        }
        """
        return self._request(query, {"eventId": str(event_id)})
