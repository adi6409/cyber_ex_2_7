from dataclasses import dataclass
from enum import Enum
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class ParamTypes(Enum):
    FILE = "file"
    STRING = "string"


@dataclass
class Request:
    client_version: str
    action: str
    params: dict
    protocol_version: str = None

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        if isinstance(json_str, str):
            data = json.loads(json_str)
            return Request(**data)
        elif isinstance(json_str, dict):
            return Request(**json_str)

@dataclass
class Response:
    success: bool
    message: str
    type: ParamTypes = ParamTypes.STRING
    slave_version: str = None
    server_version: str = None
    protocol_version: str = None

    def to_json(self):
        return json.dumps(self.__dict__, cls=CustomJSONEncoder)

    @staticmethod
    def from_json(json_str):
        if isinstance(json_str, str):
            data = json.loads(json_str)
            data['type'] = ParamTypes(data['type']) if 'type' in data else ParamTypes.STRING
            return Response(**data)
        elif isinstance(json_str, dict):
            data = json_str
            data['type'] = ParamTypes(data['type']) if 'type' in data else ParamTypes.STRING
            return Response(**data)

@dataclass
class Param:
    name: str
    type: ParamTypes = ParamTypes.STRING

    def to_dict(self):
        return {"name": self.name, "type": self.type.value}

    @staticmethod
    def from_dict(data):
        return Param(name=data['name'], type=ParamTypes(data['type']))

@dataclass
class Action:
    name: str
    params: list  # List of Param objects
    response_type: ParamTypes = ParamTypes.STRING
    function: callable = None

    def to_dict(self):
        return {
            "name": self.name,
            "params": [param.to_dict() for param in self.params],
            "response_type": self.response_type.value,
        }

    @staticmethod
    def from_dict(data):
        return Action(
            name=data['name'],
            params=[Param.from_dict(param) for param in data['params']],
            response_type=ParamTypes(data['response_type']),
        )
