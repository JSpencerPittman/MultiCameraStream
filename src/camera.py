import json


class Camera(object):
    def __init__(self, name, host, port, uri=None):
        self.name = name
        self.uri = uri
        self.host = host
        self.port = port

    @classmethod
    def from_json(Camera, cam_json):
        name = cam_json["CameraName"]
        host = cam_json["Host"]
        port = cam_json["Port"]

        uri = cam_json["URI"] if "URI" in cam_json.keys() else None

        return Camera(name, host, port, uri)

    def __str__(self):
        uri_mention = f" from {self.uri}" if self.uri is not None else ""
        return f"{self.name} on rtp:{self.host}:{self.port}{uri_mention}"

    def __repr__(self):
        return self.__str__()
