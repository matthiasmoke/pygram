
from typing import List
from _ast import Subscript, Name, Tuple, Constant, Attribute
import logging

logger = logging.getLogger("main")

class TypeInfo:

    def __init__(self, annotation_node = None, label: str = "") -> None:
        self._label: str = label
        self._contained_types: List[TypeInfo] = []
        if annotation_node is not None:
            self._create_from_annotation_node(annotation_node)
        self.fully_qualified_name: str = ""
    
    def __str__(self) -> str:
        if self.fully_qualified_name == self._label or self.fully_qualified_name == "":
            return self._label
        else:
            return self.fully_qualified_name
    
    def get_label(self) -> str:
        return self._label
    
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
            if self.is_dict():
                    return object_type._contained_types[1]
            if tuple_index > 0 and object_type.is_tuple_or_dict():
                # always return the second index for Dict objects
                return object_type._contained_types[tuple_index]
            
            return object_type
        except IndexError:
            logger.error("Can not access contained type as tuple index {} exceeds contained types (len: {})"
            .format(tuple_index, len(self._contained_types)))
    
    def _get_contained_type(self, depth: int) -> "TypeInfo":
        if depth == 0 or (self.is_tuple_or_dict() and depth == 1):
            return self

        try:
            current_child = self._contained_types[0]
            for i in range(1, depth):
                # when requested type is within tuple or dict ignore depth and return it
                if current_child.is_tuple_or_dict() and (depth - i == 1):
                    return current_child
                # if current type is dict, use second contained type, ant not the first as it is the key
                elif current_child.is_dict():
                    current_child = current_child._contained_types[1]
                else:
                    current_child = current_child._contained_types[0]

        except IndexError:
            logger.warning("Insufficient number of children contained in type respective to the requested depth.")
            return None
        return current_child
    
    def is_tuple_or_dict(self) -> bool:
        return self._label == "Dict" or self._label == "Tuple"
    
    def is_dict(self) -> bool:
        return self._label == "Dict"
    
    def _create_from_annotation_node(self, node) -> None:
        if isinstance(node, Name):
            self._label = node.id
        elif isinstance(node, Constant):
            self._label = node.value
        elif isinstance(node, Subscript):
            self._label = node.value.id
            contained = self._get_type_from_subscript(node)
            self.set_contained_types(contained)
        elif isinstance(node, Attribute):
            name: str = self._get_name_from_attribute(node)
            self._label = name
    
    def _get_name_from_attribute(self, node: Attribute) -> str:
        name: str = node.attr
        prefix: str = ""
        if isinstance(node.value, Name):
            prefix = node.value.id
        elif isinstance(node.value, Attribute):
            prefix = self._get_name_from_attribute(node.value)
        
        return "{}.{}".format(prefix, name)
    
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
        """
        Get types contained within tuple node
        """
        types: List[TypeInfo] = []
        for type_node in node.elts:
            if isinstance(type_node, Name):
                types.append(TypeInfo(label=type_node.id))
            if isinstance(type_node, Subscript):
                contained_type: TypeInfo = TypeInfo(label=type_node.value.id)
                sub_types: List[TypeInfo] = self._get_type_from_subscript(type_node)
                contained_type.set_contained_types(sub_types)
                types.append(contained_type)
        return types
