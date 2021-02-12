from typing import Any

from checker.base.rules import Followable


class CheckerMeta(type):

    def __new__(cls, *args, **kwargs):
        class_attrs = args[-1]
        rules = {}
        for attr_name, attr_value in class_attrs.items():
            if isinstance(attr_value, Followable):
                rules[attr_name] = attr_value
        
        for rule_name in rules:
            class_attrs.pop(rule_name)

        class_attrs["_rules"] = rules
        instance = super().__new__(cls, *args, **kwargs)
        return instance


class BaseChecker(metaclass=CheckerMeta):
    """Базовый класс для проверки объекта по набору правил."""

    def __init__(self, obj: Any):
        self._obj = obj
    
    def check(self):
        """Выполняет проверку объекта по указанным правилам."""
        for rule_name, rule in self._rules.items():
            if hasattr(rule, "obj"):
                rule.obj = self._obj
            
            rule.follow()