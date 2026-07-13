import json
import zipfile
from pathlib import Path
from statistics import mean


def _get_resource_category(entry):
    """
    Find out if the given HAR entry is a XHR, JS or image request.
    Uses the request headers
    :param entry: a single HAR "entries" element
    :return: 'xhr', 'js', 'image', 'html' or None if the entry is none of these types
    """

    mime_type = (entry.get('response', {}).get('content', {}).get('mimeType') or '').lower()
    if 'javascript' in mime_type or 'ecmascript' in mime_type:
        return 'js'
    if mime_type.startswith('image/'):
        return 'image'
    if 'json' in mime_type:
        return 'xhr'
    if 'html' in mime_type:
        return 'html'

    headers = entry.get('request', {}).get('headers', [])
    if any(header.get('name', '').lower() == 'x-requested-with' for header in headers):
        return 'xhr'

    return None


def _load_har(har_file):
    """
    Load a HAR file into a dict, whatever the input format is
    :param har_file: path to a '.har' or '.har.zip' file (str or Path), raw bytes/str of a HAR file content,
                      or an already parsed HAR dict
    :return: the parsed HAR content as a dict
    """
    if isinstance(har_file, dict):
        return har_file

    if isinstance(har_file, (bytes, bytearray, str)) and not Path(str(har_file)).exists():
        content = har_file
    else:
        path = Path(har_file)
        content = path.read_bytes()

    return json.loads(content)


def get_average_request_time_per_page(har_file):
    """
    Compute, for each page of the HAR file, the average request time (in milliseconds) of XHR, JS and image
    requests. Other request types (document, css, font, ...) are ignored.
    :param har_file: path to a '.har' or '.har.zip' file (str or Path), raw bytes/str of a HAR file content,
                      or an already parsed HAR dict
    :return: dict {page_title: average_time_in_ms}, pages without any matching request are omitted
    """
    har = _load_har(har_file)
    log = har.get('log', {})
    page_names = {page['id']: page.get('title') or page['id'] for page in log.get('pages', [])}

    times_by_page = {}
    for entry in log.get('entries', []):
        category =_get_resource_category(entry)
        if category is None:
            continue

        pageref = entry.get('pageref')
        page_name = page_names.get(pageref, pageref or 'unknown')

        time_ms = entry.get('time')
        if time_ms is None or time_ms < 0:
            continue

        # /!\ if 2 pages have the same name, all load times will be merged
        times_by_page.setdefault(page_name, {'xhr': [], 'js': [], 'image': [], 'html': []})[category].append(time_ms)

    return {page: {category: round(mean(times), 2) for category, times in times_by_category.items() if times} for page, times_by_category in times_by_page.items() }
