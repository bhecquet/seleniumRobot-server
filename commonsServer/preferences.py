import logging

from django.core.cache import cache

from commonsServer.models import AppPreference

CACHE_PREFIX = "app_pref:"

DEFAULT_PREFERENCES = {
    "MISTRAL_DOC_COMPARISON_SYSTEM_PROMPT": {
        "value": """
    The document that you get is the result of 2 documents concatenation. They must be compared.
    First document is on %(page_number_1)d pages
    Second document is on %(page_number_2)d pages
    
    You will compare the first  %(page_number_1)d pages (first document) with the next %(page_number_2)d pages (second document)
    
    For example, if the first document has 3 pages, and second document has 2 pages, you get a 5 pages document. And you must compare the content of pages 1, 2 and 3 with the content of page 4 and 5.
    To perform this comparison, read all the 3 pages (1, 2, 3) as a whole, and try to find what are the differences with pages 4 and 5. Never read page 4 and 5 to try to find differences with pages 1, 2 and 3
    
    In the case of a multi pages document, some information may be repeated at the top and the bottom of each page, you should not consider them as differences
    """,
        "description": "System prompt send to mistral for document comparison. Can use '%(page_number_1)d and %(page_number_2)d placeholders",
    },

    "MISTRAL_DOC_COMPARISON_DIFFERENCES_PROMPT": {
        "value": """List differences between the 2 documents.
Find differences, one after the other, from top to bottom. **STOP when you reach 20 differences**
 For each difference, you will give the page and the position of the difference, and a description of that difference. 
The whole answer will be a JSON with the format:
 ```
 [
 {"page": <page_number_as_integer>, 
 "location": <location_description>,
 "details": <details_about_difference>
 },
 ...
 <other differences>
 ...
 ]
 ```
 If no difference is found, return an empty list
 """,
        "description": "Prompt to tell Mistral doc annotation model how to list differences between the 2 documents"},

    # ----------------------------------------------------------
    # Clean job parameters
    # ----------------------------------------------------------

    "DELETE_STEP_REFERENCE_AFTER_DAYS":
        {"value": "30", "description": "number of days after which old references will be deleted if they have not been updated. 30 days by default"},
    "COMPRESS_IMAGE_FOR_SUCCESS_AFTER_DAYS":
        {"value": "5", "description": "number of days after which images of successful tests (except step references and snapshot for comparison) will be compressed at 85%"},
    "COMPRESS_IMAGE_FOR_FAILURE_AFTER_DAYS":
        {"value": "10", "description": "number of days after which images of failed tests (except step references and snapshot for comparison) will be compressed at 85%"},
    "DELETE_HTML_FOR_SUCCESS_AFTER_DAYS":
        {"value": "5", "description": "number of days after which HTML of successful tests will be replaced by empty code"},
    "DELETE_HTML_FOR_FAILURE_AFTER_DAYS":
        {"value": "10", "description": "number of days after which HTML of failed tests will be replaced by empty code"},
    "DELETE_VIDEO_FOR_SUCCESS_AFTER_DAYS":
        {"value": "15", "description": "number of days after which video of successful tests will be deleted"},
    "DELETE_HAR_FOR_SUCCESS_AFTER_DAYS":
        {"value": "7", "description": "number of days after which HAR of successful tests captures will be deleted"},
    "CLEANING_CRON":
        {"value": "0 3 * * *", "description": "clean every day at 3 a.m"},
    "VAR_UPLOAD_FILE_MAX_SIZE":
        {"value": "10000000", "description": "allow files as variable value up to 10 MB to be uploaded"},
    "VAR_UPLOAD_EXTENSIONS":
        {"value": "csv,xls,xlsx,json,txt,pdf", "description": "Comma-separated list of allowed extensions"},
    "VAR_UPLOAD_FILE_MIMETYPES":
        {"value": "text/plain,application/json,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,application/pdf", 'description': 'Comma-separated list of mimetypes that will be allowed for files as variables'},

    # ----------------------------------------------------------
    # Image detection parameters
    # ----------------------------------------------------------

    "OPEN_WEBUI_PROMPT_FIND_ERROR_MESSAGE":
        {"value": '''In the provided image, do you see an error message ?
- Start by extracting all texts and their color
- Then, for each text, depending on its colour and meaning, determine if the text is an error message

Reply only in JSON, with the following format:
```
{"explanation": "<what leads to your conclusion>", "error_messages": [<list of detected error messages or technical failures as STRING]}
```
‘error_messages’ key may have an empty value if no error message or technical failure has been detected
Check that the JSON response is valid''', "description": "Prompt to use for finding error messages on pictures"},

    "OPEN_WEBUI_PROMPT_WEBPAGE_COMPARISON":
{"value": '''You are a tester that wants to check a test result.
These 2 pictures represent web pages.
Your goal is to say if the 2 pictures are from the same web page (even if some textual information differ).
You will base your response on:
- page layout / content layout
- general design
- position of graphical elements like buttons, text fields, tabs
- color scheme of graphical elements

Your response should NOT be based on:
- text data that may vary from user or customer

You will consider that the 2 pictures represent the same web page with a percentage of confidence (100% same page, 0% not the same page) if layout, general design, position and color of graphical elements look similar.

Reply only in JSON, with the following format:
```
{"explanation": "<what leads to your conclusion>", "similarity": <percentage of confidence as INTEGER>}
```
Check that the JSON response is valid
''', "description": "Prompt that will be used for image comparison"},

    "OPEN_WEBUI_PROMPT_FIND_ELEMENT":
{"value": '''In the provided picture, tell me if the %s is present or not.
For this:
- analyze the picture, looking for text fields, buttons, tabs and texts
- say if the requested field is present

Reply only in JSON, with the following format:
```
{"explanation": "<what leads to your conclusion>", "present": <true/false>}
```
Check that the JSON response is valid
''', "description": "Prompt that will be used to find element on a picture"},

    "OPEN_WEBUI_MODEL":
        {"value": 'ministral-3:8b', 'description': 'model to use for picture inference (comparison / find element / error message)'},
    "OPEN_WEBUI_WORKERS":
        {"value": '2', 'description': 'Number of parallel workers'}
}

logger = logging.getLogger(__name__)

def _cache_key(key: str) -> str:
    return f"{CACHE_PREFIX}{key}"


def sync_defaults():
    for key, meta in DEFAULT_PREFERENCES.items():
        app_preference = AppPreference.objects.get_or_create(
            key=key,
            defaults={
                # initial value and value will have the same value on first sync
                "initialValue": str(meta.get("value", "")),
                "value": str(meta.get("value", "")),
                "description": meta.get("description", ""),
            },
        )[0]

        # update initial value in case it's difference in database
        # also update value if it's the same as initial value
        if app_preference.initialValue != str(meta.get("value", "")):
            if app_preference.value == app_preference.initialValue:
                app_preference.value = str(meta.get("value", ""))
            app_preference.initialValue = str(meta.get("value", ""))
            app_preference.save()


def get_preference(key: str):
    ck = _cache_key(key)
    cached = cache.get(ck)
    if cached is not None:
        return cached

    try:
        val = AppPreference.objects.only("value").get(key=key).value
    except AppPreference.DoesNotExist:
        sync_defaults()
        val = AppPreference.objects.only("value").get(key=key).value

    if val is not None:
        cache.set(ck, val)

    if val is None:
        logger.error(f"Preference '{key}' does not exist")

    return val

def set_preference(key: str, value: str):
    """
    To be used in tests
    :param key:
    :param value:
    :return:
    """
    ck = _cache_key(key)
    if value is not None:
        cache.set(ck, value)

def invalidate_pref_cache(key: str):
    cache.delete(_cache_key(key))


def invalidate_all_pref_cache():
    keys = list(AppPreference.objects.values_list("key", flat=True))
    for k in keys:
        cache.delete(_cache_key(k))

