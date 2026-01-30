import json
from typing import Any, Dict, Optional

import requests

API_BASE_URL = "https://genome.crg.es/annotrieve/api/v0"


def core_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Make a request to the Annotrieve API.

    Args:
        endpoint: API endpoint (e.g., '/annotations')
        method: HTTP method ('GET' or 'POST')
        params: Query parameters for GET requests
        json_data: JSON body for POST requests

    Returns:
        JSON response as dictionary
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")


def make_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    
    params = dict(params or {})

    response = core_request(endpoint, method, params, json_data)
    total = response.get("total", None)

    if not total:
        return response

    collected = len(response["results"])
    params["offset"] = collected
    
    while collected < total:
        next_response = core_request(endpoint, method, params, json_data)
        next_results = next_response.get("results", [])    
    
        if not next_results:
            break

        response["results"].extend(next_results)
        collected += len(next_results)
        params["offset"] += len(next_results)

    response["offset"] = 0
    response["total"] = total
    return response



def get_filename_from_url(url, base_name):
    """Generate filename as base_name with extension from URL."""
    filename_part = url.split("/")[-1]
    if "." in filename_part:
        ext = "." + ".".join(filename_part.split(".")[1:])
    else:
        ext = ""
    return f"{base_name}{ext}"


def download_file(url, filepath):
    """Download file from URL to filepath."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
