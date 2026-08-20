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


def get_network_info_per_page(har_file):
    """
    Compute, for each page of the HAR file, network information:
    - 'times': the average request time (in milliseconds) of XHR, JS, HTML and image requests. Other request
      types (document, css, font, ...) are ignored
    - 'errors': the list of requests that failed on that page, i.e. requests that got no response at all, or
      whose response has a 4xx or 5xx HTTP status code. Each error is a dict
      {'url': <request_url>, 'status': <response_status_or_None>, 'statusText': <response_status_text_or_None>}
    :param har_file: path to a '.har' or '.har.zip' file (str or Path), raw bytes/str of a HAR file content,
                      or an already parsed HAR dict
    :return: dict {page_title: {'times': {...}, 'errors': [...]}}, pages with neither a matching request nor an
             error are omitted
    """
    har = _load_har(har_file)
    log = har.get('log', {})
    page_names = {page['id']: page.get('title') or page['id'] for page in log.get('pages', [])}

    data_by_page = {}
    for entry in log.get('entries', []):
        pageref = entry.get('pageref')
        page_name = page_names.get(pageref, pageref or 'unknown')
        page_data = data_by_page.setdefault(page_name, {'times': {'xhr': [], 'js': [], 'image': [], 'html': []}, 'errors': []})

        category = _get_resource_category(entry)
        if category is not None:
            time_ms = entry.get('time')
            if time_ms is not None and time_ms >= 0:
                page_data['times'][category].append(time_ms)

        response = entry.get('response')
        status = response.get('status') if response else None

        # no response at all (status missing or 0) or a 4xx / 5xx status is considered a network error
        if not response or not status or status >= 400:
            page_data['errors'].append({
                'url': entry.get('request', {}).get('url'),
                'status': status or None,
                'statusText': (response or {}).get('statusText') or None,
            })

    result = {}
    for page_name, page_data in data_by_page.items():
        times = {category: round(mean(times), 2) for category, times in page_data['times'].items() if times}
        if not times and not page_data['errors']:
            continue

        result[page_name] = {'times': times, 'errors': page_data['errors']}

    return result
