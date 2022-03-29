
from typing import List
from _ast import Subscript, Name, Tuple, Constant, Attribute
import logging

from ..utils import Utils

logger = logging.getLogger("main")

class TypeInfo:

    def __init__(self, annotation_node = None, label: str = "") -> None:
        self.label: str = label
        self._contained_types: List[TypeInfo] = []
        if annotation_node is not None:
            self._create_from_annotation(annotation_node)
        self.fully_qualified_name: str = ""
    
    def __str__(self) -> str:
        if self.fully_qualified_name == self.label or self.fully_qualified_name == "":
            return self.label
        else:
            return self.fully_qualified_name
    
    def get_label(self) -> str:
        return self.label
    
    def get_contained_types(self) -> List["TypeInfo"]:
        return self._contained_types
    
    def set_fully_qualified_name(self, name: str) -> None:
        self.fully_qualified_name = name

    def set_contained_types(self, type_info_list: List["TypeInfo"]) -> None:
        self._contained_types = type_info_list
    
    def get_type(self, depth: int, tuple_index: int) -> "TypeInfo":
        object_type: TypeInfo = self._get_contained_type(depth)

        if object_type is None:
            return None

        try:
            if object_type.is_dict() and depth == 0:
                # as depth is 0 and the object is a dict, the call happens on the dictionary not the contained types
                return self
            if object_type.is_dict() and depth == 1:
                # always return the second index for Dict objects
                return object_type._contained_types[1]
            if object_type.is_tuple_or_dict():
                return object_type._contained_types[tuple_index]
            
            return object_type
        except IndexError:
            logger.error("Can not access contained type as tuple index {} exceeds contained types (len: {})"
            .format(tuple_index, len(self._contained_types)))
    
    def _get_contained_type(self, depth: int) -> "TypeInfo":
        if depth == 0 or (self.is_tuple_or_dict() and depth == 1):
            return self

        try:
            current_child: TypeInfo = self._contained_types[0]
            for i in range(1, depth):
                # when requested type is within tuple or dict ignore depth and return it
                if current_child.is_tuple_or_dict() and (depth - i == 1):
                    return current_child
                # if current type is dict, use second contained type, ant not the first as it is usually the key
                elif current_child.is_dict():
                    current_child = current_child._contained_types[1]
                else:
                    current_child = current_child._contained_types[0]

        except IndexError:
            logger.warning("Insufficient number of children contained in type respective to the requested depth.")
            return None
        return current_child
    
    def is_tuple_or_dict(self) -> bool:
        return self.is_dict() or self.label == "Tuple"
    
    def is_dict(self) -> bool:
        return self.label == "Dict"
    
    def _create_from_annotation(self, node) -> None:
        if isinstance(node, Name):
            self.label = node.id
        elif isinstance(node, Constant):
            self.label = node.value
        elif isinstance(node, Subscript):
            self.label = Utils.get_name_from_subscript(node)
            contained = self._get_type_from_subscript(node)
            self.set_contained_types(contained)
        elif isinstance(node, Attribute):
            name: str = Utils.get_full_name_from_attribute_node(node)
            self.label = name
    
    def _get_type_from_subscript(self, node: Subscript) -> List["TypeInfo"]:
        slice = node.slice
        contained_types: List[TypeInfo] = []

        if isinstance(slice, Name):
            contained_types.append(TypeInfo(label=slice.id))
        elif isinstance(slice, Subscript):
            label: str = Utils.get_name_from_subscript(slice)
            contained_type: TypeInfo = TypeInfo(label=label)
            result = self._get_type_from_subscript(slice)
            contained_type.set_contained_types(result)
            contained_types.append(contained_type)
        elif isinstance(slice, Tuple):
            contained_types = self._get_tuple_types(slice)
        
        return contained_types

    def _get_tuple_types(self, node: Tuple) -> List["TypeInfo"]:
        """
        Get types contained within tuple node
        """
        types: List[TypeInfo] = []
        for type_node in node.elts:
            if isinstance(type_node, Name):
                types.append(TypeInfo(label=type_node.id))
            if isinstance(type_node, Subscript):
                label = Utils.get_name_from_subscript(type_node)
                contained_type: TypeInfo = TypeInfo(label=label)
                sub_types: List[TypeInfo] = self._get_type_from_subscript(type_node)
                contained_type.set_contained_types(sub_types)
                types.append(contained_type)
        return types
