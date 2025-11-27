import json


class ObjectJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, 'url'):
            return obj.url
        return super().default(obj)

