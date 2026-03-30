import os
from typing import List, Dict, Any
from serpapi import GoogleSearch
import logging

log = logging.getLogger("serpapi")

class SerpApiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")

    def fetch_places(self, query: str, location: str = "Port Moresby") -> List[Dict[str, Any]]:
        if not self.api_key:
            log.warning("SERPAPI_KEY not set. Returning empty list.")
            return []

        # We combine query and location for better results on Google Maps engine
        # e.g. "schools Port Moresby"
        search_query = f"{query} {location}"

        params = {
            "engine": "google_maps",
            "q": search_query,
            "ll": "@-9.4438,147.1803,13z", # Centered on Port Moresby
            "type": "search",
            "api_key": self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            if "error" in results:
                log.error(f"SerpApi Error: {results['error']}")
                return []

            local_results = results.get("local_results", [])
            places = []
            for res in local_results:
                gps = res.get("gps_coordinates", {})
                places.append({
                    "name": res.get("title"),
                    "type": res.get("type"),
                    "rating": res.get("rating"),
                    "reviews": res.get("reviews"),
                    "address": res.get("address"),
                    "lat": gps.get("latitude"),
                    "lng": gps.get("longitude")
                })
            return places
        except Exception as e:
            log.error(f"Failed to fetch places from SerpApi: {e}")
            return []

def get_serpapi_places(category: str) -> List[Dict[str, Any]]:
    client = SerpApiClient()
    # Map friendly categories to search queries
    queries = {
        "schools": "schools",
        "hospitals": "hospitals and clinics",
        "supermarkets": "supermarkets",
        "police": "police stations",
        "banks": "banks and atms"
    }
    query = queries.get(category.lower(), category)
    return client.fetch_places(query)
