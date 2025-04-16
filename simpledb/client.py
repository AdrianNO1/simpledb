import requests
from requests.exceptions import HTTPError, ConnectionError

BASE_URL = "http://127.0.0.1:6924"

def set_base_url(new_url):
    """Sets the base URL for the SimpleDB API client."""
    global BASE_URL
    BASE_URL = new_url

METADATA_KEYS = {"created_at", "created_by", "updated_at", "updated_by"}

def _strip_metadata(item):
    """Recursively strips metadata keys and extracts 'value' if present."""
    if isinstance(item, dict):
        if "value" in item and all(k in METADATA_KEYS or k == "value" for k in item.keys()):
            # file
            return item["value"]
        else:
            # folder
            return {k: _strip_metadata(v) for k, v in item.items() if k not in METADATA_KEYS}
    elif isinstance(item, list):
        # list
        return [_strip_metadata(elem) for elem in item]
    else:
        return item

def read(path, include_metadata=False):
    """Gets a value or folder structure. Returns None if not found."""
    url = f"{BASE_URL}/read/{path}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if include_metadata:
            return data
        else:
            return _strip_metadata(data)
    except HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise
    except ConnectionError:
        raise RuntimeError("Could not connect to the SimpleDB server. Is it running?")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def write(path, value):
    """Writes a value and returns the set value on success."""
    url = f"{BASE_URL}/write/{path}"
    try:
        response = requests.put(url, json={"value": value})
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("metadata", {}).get("value")
    except ConnectionError:
        raise RuntimeError("Could not connect to the SimpleDB server. Is it running?")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def delete_value(path):
    """Deletes a value and returns the deleted value on success."""
    url = f"{BASE_URL}/delete_value/{path}"
    try:
        response = requests.delete(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except ConnectionError:
        raise RuntimeError("Could not connect to the SimpleDB server. Is it running?")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def delete_folder(path):
    """Deletes a folder and returns the deleted content on success."""
    url = f"{BASE_URL}/delete_folder/{path}"
    try:
        response = requests.delete(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except ConnectionError:
        raise RuntimeError("Could not connect to the SimpleDB server. Is it running?")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise 