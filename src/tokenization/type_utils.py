from typing import List, Dict, Any
from _ast import Subscript, Name, Tuple

class TypeInfo:

    def __init__(self, annotation_node) -> None:
        self.top_level_type: str = ""
        self.sub_types: Dict[int, Any] = {}
        self.create_from_ann_assign(annotation_node)
    
    def get_type(self) -> str:
        return self.top_level_type
    
    def _set_top_level_type(self, type):
        self.top_level_type = type
        self.sub_types[0] = type
    
    def create_from_ann_assign(self, node):
        if isinstance(node, Name):
            self.top_level_type = node.id
            self.sub_types[0] = node.id
        elif isinstance(node, Subscript):
            self.top_level_type = node.value.id
            self._get_type_from_subscript(node, self.sub_types, 0)
    
    def _get_type_from_subscript(self, node: Subscript, type_list: Dict[int, Any], depth: int):
        top_type = node.value.id
        type_list[depth] = top_type
        depth += 1
        slice = node.slice.value

        if isinstance(slice, Name):
            type_list[depth] = slice.id
        elif isinstance(slice, Subscript):
            self._get_type_from_subscript(slice, type_list, depth + 1)
        elif isinstance(slice, Tuple):
            types: Dict[int, Any] = self._get_tuple_type(slice)
            tuple_type = TupleType(top_type, types)
            type_list[depth] = tuple_type

    
    def _get_tuple_type(self, node: Tuple) -> Dict[int, Any]:
        types: Dict[int, Any] = {}
        for index, type_node in enumerate(node.elts):
            if isinstance(type_node, Name):
                types[index] = type_node.id
            if isinstance(type_node, Subscript):
                sub_types: Dict[str, Any] = {}
                self._get_type_from_subscript(type_node, sub_types, 0)
                types[index] = sub_types
        return types



class TupleType():

    def __init__(self, top_level_type: str, tuple_types: Dict[int, Any]) -> None:
        self.top_level_type: str = top_level_type
        self.tuple_types: Dict[int, Any] = tuple_types
    
    def get_type(self):
        return self.top_level_type

    def get_tuple_type(self, index):
        return self.tuple_types[index]