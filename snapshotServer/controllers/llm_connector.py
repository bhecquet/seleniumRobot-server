import base64
import logging
import os
from io import BytesIO

import requests
from PIL import Image
from django.conf import settings
from openwebui_chat_client import OpenWebUIClient

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

    def chat(self, prompt: str, image_paths: list, resize_factor: int =100):
        """
        Call open-webui to ask for LLM response
        If no response is given, returns a dict with error message

        :param prompt:      prompt to submit
        :param image_paths:  a list of files to include into the prompt
        :return:
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
                json_response = response.json()
                json_response['error'] = ''
                return json_response
            except Exception as e:
                return {'error': "Error chating with Open WebUI: " + str(e)}
        else:
            return {'error': 'Open WebUI not available'}