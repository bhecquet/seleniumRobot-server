import base64
import json
import logging
import os
from collections import namedtuple
from io import BytesIO

import requests
from PIL import Image
from django.conf import settings
from openwebui_chat_client import OpenWebUIClient

ChatJsonResponse = namedtuple('ChatJsonResponse', ['response', 'error'])

logger = logging.getLogger(__name__)

class LlmConnector:

    open_web_ui_client = None

    def __init__(self):

        if settings.OPEN_WEBUI_URL and settings.OPEN_WEBUI_TOKEN and settings.OPEN_WEBUI_MODEL:
            self.open_web_ui_client = OpenWebUIClient(
                base_url=settings.OPEN_WEBUI_URL,
                token=settings.OPEN_WEBUI_TOKEN,
                default_model_id=settings.OPEN_WEBUI_MODEL
            )

    def chat_and_expect_json_response(self, prompt: str, image_paths: list, resize_factor: int =100) -> ChatJsonResponse:
        """
        Call LLM expecting that the prompt produces a JSON object
        This JSON will be read and returned
        :param prompt:          prompt to submit
        :param image_paths:     a list of files to include into the prompt
        :param resize_factor:   whether images should be resized before being submitted to LLM
        :return: <response as dict or None is error occurs>, <error or None>
        """

        result = self.chat(prompt, image_paths, resize_factor)
        llm_error = result.get('error', '')

        if 'choices' in result and len(result['choices']) > 0:
            logger.info("LLM response in %.2f secs" % (result['usage']['total_duration'] / 1000000000.,))
            response_str = result['choices'][0]['message']['content'].replace('```json', '').replace('```', '')
            try:
                return ChatJsonResponse(json.loads(response_str.replace('\n', '')), None)
            except Exception:
                return ChatJsonResponse(None, "Invalid JSON returned by model")

        else:
            logger.error("No response from Open WebUI: " + llm_error)
            return ChatJsonResponse(None, "No response from Open WebUI:" + llm_error)

    def chat(self, prompt: str, image_paths: list, resize_factor: int =100) -> dict:
        """
        Call open-webui to ask for LLM response
        If no response is given, returns a dict with error message

        :param prompt:          prompt to submit
        :param image_paths:     a list of files to include into the prompt
        :param resize_factor:   whether images should be resized before being submitted to LLM
        :return: a dict of the response. dict will always have an 'error' key
        """
        if self.open_web_ui_client and len(self.open_web_ui_client.list_models()) > 0:

            headers = {
                'Authorization': f'Bearer {settings.OPEN_WEBUI_TOKEN}',
                'Content-Type': 'application/json'
            }
            data = {
                "model": settings.OPEN_WEBUI_MODEL,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }]
            }

            for image_path in image_paths:
                if os.path.isfile(image_path):
                    img = Image.open(image_path)
                    if resize_factor != 100:
                        resized = img.resize((int(img.width * resize_factor/100.), int(img.height * resize_factor/100.)), Image.LANCZOS)
                    else:
                        resized = img
                    buffered = BytesIO()
                    resized.save(buffered, format="PNG")

                    data['messages'][0]['content'].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")
                            }
                        })

            try:
                response = requests.post(settings.OPEN_WEBUI_URL + '/api/chat/completions', headers=headers, json=data)
                if response.status_code == 200:
                    json_response = response.json()
                    json_response['error'] = ''
                    return json_response
                else:
                    return {'error': "Error chating with Open WebUI: " + str(response.text)}
            except Exception as e:
                return {'error': "Error chating with Open WebUI: " + str(e)}
        else:
            return {'error': 'Open WebUI not available'}