# app/controllers/base_controller.py
from typing import TypeVar, Generic, Optional
from abc import ABC

T = TypeVar('T')


class BusinessException(Exception):
    """业务异常类"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(self.message)


class BaseController(ABC):
    """控制器基类"""

    def _validate_required_fields(self, data: dict, required_fields: list):
        """验证必需字段"""
        for field in required_fields:
            if field not in data or data[field] is None:
                raise BusinessException(f"字段 '{field}' 是必需的")

    def _validate_string_length(self, value: str, field_name: str, max_length: int = None, min_length: int = None):
        """验证字符串长度"""
        if value is None:
            return

        if min_length and len(value) < min_length:
            raise BusinessException(f"字段 '{field_name}' 长度不能少于 {min_length} 个字符")

        if max_length and len(value) > max_length:
            raise BusinessException(f"字段 '{field_name}' 长度不能超过 {max_length} 个字符")