from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Dict, Tuple, MutableMapping, Union, List


class Output(ABC):
    @abstractmethod
    def start_module(self, name: str):
        pass

    @abstractmethod
    def method(
        self,
        method: str,
        description: str,
        parameters: Union[MutableMapping[str, Tuple[str, str]], OrderedDict],
        return_values: Union[MutableMapping[str, Tuple[str, str]], OrderedDict],
    ):
        pass

    @abstractmethod
    def start_class(self, name: str):
        pass

    @abstractmethod
    def class_properties(self, properties: List[str]):
        pass

    @abstractmethod
    def class_methods(self, methods: List[str]):
        pass

    @abstractmethod
    def start_unknown_class(self, name: str):
        pass
