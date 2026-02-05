import orjson
from rest_framework.renderers import JSONRenderer

class ORJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''
        
        return orjson.dumps(data)
