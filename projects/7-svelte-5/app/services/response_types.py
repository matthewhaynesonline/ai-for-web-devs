from dataclasses import dataclass
# from enum import Enum as StandardEnum
# from typing import List


# Tried to dynamically generate the dataclass from the enum
# but in the end it wasn't worth it, since in order to get
# type hinting support, it needed a .pyi file, so just write it
# out instead of using metaprogramming
# ResponseTypesFlags = ResponseTypes.create_type_flags_class()

# class ResponseTypes(StandardEnum):
#     """
#     Pardon the metaprogramming, but this enum is the source of truth
#     for the message types that are currently supported. The flags data class
#     and the JSON schema for the classification LLM call will be built from
#     this enum
#     """

#     IMAGE = "image"
#     TEXT = "text"
#     # AUDIO = "audio"
#     # VIDEO = "video"

#     @classmethod
#     def values(cls) -> List[str]:
#         return [type.value for type in cls]

#     # @classmethod
#     # def create_type_flags_class(cls) -> Type:
#     #     fields = [(f"is_{value.lower()}", bool) for value in cls.values()]
#     #     return make_dataclass("ResponseTypesFlags", fields)


@dataclass
class ResponseTypesFlags:
    is_image: bool = False
    is_text: bool = False
