
from typing import Dict, List
from _ast import Subscript, Name, Tuple, AnnAssign
import logging

logger = logging.getLogger("main")

class TypeInfo:

    def __init__(self, node: AnnAssign = None, label: str = "") -> None:
        self._label: str = label
        self._contained_types: List[TypeInfo] = []
        if node is not None:
            self._create_from_ann_assign(node)
    
    def get_label(self) -> str:
        return self._label
    
    def set_contained_types(self, type_info_list: List["TypeInfo"]) -> None:
        self._contained_types = type_info_list
    
    def get_type(self, depth: int, tuple_index: int) -> "TypeInfo":
        object_type = self._get_contained_type(depth)

        if object_type is None:
            return None

        if self._is_dict(object_type):
                return object_type._contained_types[1]
        if tuple_index > 0 and self._is_tuple_or_dict(object_type):
            # always return the second index for Dict objects
            return object_type._contained_types[tuple_index]
        
        return object_type
    
    def _get_contained_type(self, depth: int) -> "TypeInfo":
        if depth == 0 or (self._is_tuple_or_dict(self) and depth == 1):
            return self

        try:
            current_child = self._contained_types[0]
            for i in range(1, depth):
                # when requested type is within tuple or dict ignore depth and return it
                if self._is_tuple_or_dict(current_child) and (depth - i == 1):
                    return current_child
                current_child = current_child._contained_types[0]

        except IndexError:
            logger.warning("Insufficient number of children contained in type respective to the requested depth.")
            return None
        return current_child
    
    def _is_tuple_or_dict(self, type_info: "TypeInfo") -> bool:
        return type_info._label == "Dict" or type_info._label == "Tuple"
    
    def _is_dict(self, type_info: "TypeInfo") -> bool:
        return type_info._label == "Dict"
    
    def _create_from_ann_assign(self, node: AnnAssign) -> None:
        if isinstance(node, Name):
            self._label = node.id
        elif isinstance(node, Subscript):
            self._label = node.value.id
            contained = self._get_type_from_subscript(node)
            self.set_contained_types(contained)
    
    def _get_type_from_subscript(self, node: Subscript) -> List["TypeInfo"]:
        slice = node.slice.value
        contained_types: List[TypeInfo] = []

        if isinstance(slice, Name):
            contained_types.append(TypeInfo(label=slice.id))
        elif isinstance(slice, Subscript):
            contained_type: TypeInfo = TypeInfo(label=slice.value.id)
            result = self._get_type_from_subscript(slice)
            contained_type.set_contained_types(result)
            contained_types.append(contained_type)
        elif isinstance(slice, Tuple):
            contained_types = self._get_tuple_types(slice)
        
        return contained_types

    def _get_tuple_types(self, node: Tuple) -> List["TypeInfo"]:
        types: List[TypeInfo] = []
        for type_node in node.elts:
            if isinstance(type_node, Name):
                types.append(TypeInfo(label=type_node.id))
            if isinstance(type_node, Subscript):
                contained_type: TypeInfo = TypeInfo(label=type_node.value.id)
                sub_types: List[TypeInfo] = self._get_type_from_subscript(type_node, sub_types, 0)
                contained_type.set_contained_types(sub_types)
                types.append(contained_type)
        return types