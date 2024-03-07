import json


class Camera(object):
    def __init__(self, name, host, port, uri=None, resize=None):
        self.name = name
        self.uri = uri
        self.host = host
        self.port = port
        self.resize = resize

    @classmethod
    def from_json(Camera, cam_json):
        name = cam_json["CameraName"]
        host = cam_json["Host"]
        port = cam_json["Port"]

        uri = cam_json["URI"] if "URI" in cam_json.keys() else None
        resize = cam_json["Resize"] if "Resize" in cam_json.keys() else None

        return Camera(name, host, port, uri, resize)
