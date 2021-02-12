from abc import ABCMeta
from abc import abstractmethod
from collections.abc import Callable
from functools import partial
from functools import update_wrapper
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Union
import operator


def lazy_exec_args(func: Callable, *args) -> Any:
    """Выполняет функцию с callable аргументами."""
    return func(
        *map(lambda f: f() if callable(f) else f, args)
    )


def wrapped_partial(func: Callable, *args, **kwargs) -> Callable:
    """Добавляет к результату partial информацию о вложенной функции."""
    partial_func = partial(lazy_exec_args, func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func


class Followable(metaclass=ABCMeta):
    """Интерфейс правила проверки."""

    @abstractmethod
    def follow(self) -> bool:
        """Проверяет соответствие правилу."""
        raise NotImplementedError()


class BitwiseRuleResult:
    """Результат выполнения побитовой операции для правила."""
    def __init__(self, func: Callable, *args):
        self._func = func
        self._args = args
        self._obj = None
    
    @property
    def obj(self):
        return self._obj
    
    @obj.setter
    def obj(self, obj):
        self._obj = obj
    
    def __call__(self) -> Any:
        for arg in self._args:
            if hasattr(arg, '__self__') and self.obj:
                arg.__self__.obj = self.obj
        
        return lazy_exec_args(self._func, *self._args)
    
    def __and__(self, rule: Union['Rule', Callable]) -> 'BitwiseRuleResult':
        if isinstance(rule, Rule):
            rule = rule._exec_func
        
        return BitwiseRuleResult(
            operator.and_,
            self,
            rule
        )
    
    def __or__(self, rule: Union['Rule', Callable]) -> 'BitwiseRuleResult':
        if isinstance(rule, Rule):
            rule = rule._exec_func
        
        return BitwiseRuleResult(
            operator.or_,
            self,
            rule
        )
    
    @property
    def __name__(self):
        return self._func.__name__


class BitwiseRuleMixin:
    """Примесь для добавления бинарных операций к правилам."""

    def __and__(self, rule: Union['Rule', Callable]) -> BitwiseRuleResult:
        if isinstance(rule, Rule):
            rule = rule._exec_func
        
        return BitwiseRuleResult(
            operator.and_,
            self._exec_func,
            rule
        )
    
    def __or__(self, rule: Union['Rule', Callable]) -> BitwiseRuleResult:
        if isinstance(rule, Rule):
            rule = rule._exec_func
        
        return BitwiseRuleResult(
            operator.or_,
            self._exec_func,
            rule
        )


class BaseRule(Followable, BitwiseRuleMixin):
    """Базовый класс для правила проверки объекта."""

    @property
    def obj(self):
        return self._obj
    
    @obj.setter
    def obj(self, obj: Any):
        self._obj = obj

    def _exec_func(self) -> bool:
        """Выполняет проверку по правилу."""
        raise NotImplementedError()

    def follow(self) -> bool:
        """Проверяет соответствие правилу."""
        if not self._exec_func():
            raise self._exc(self._msg)

        return True


class Rule(BaseRule, BitwiseRuleMixin):
    """Правило для проверки объекта."""
    def __init__(
        self,
        attribute: str,
        func: Callable,
        obj: Any = None,
        exc: Optional[Exception] = None,
        msg: Optional[str] = None
    ):
        self._obj = obj
        self._attr = attribute
        self._f = func
        self._exc = exc if exc else ValueError
        self._msg = msg if msg else f'{self._attr} не прошел проверку'
        self._obj = obj
    
    def _get_attribute_value(self) -> Any:
        """Возвращает значение атрибута проверяемого объекта."""
        attrgetter = operator.attrgetter(self._attr)
        value = attrgetter(self.obj)
        if callable(value):
            value = value()
        
        return value
    
    def _exec_func(self) -> bool:
        """Выполняет проверку по правилу."""
        value = self._get_attribute_value()
        return bool(self._f(value))


class WrappedRule(BaseRule, BitwiseRuleMixin):
    """Обертка для применения callable объектов как правил."""
    def __init__(
        self,
        rule: Callable,
        msg: Optional[str] = None,
        exc: Optional[Exception] = None,
        obj: Any = None,
    ):
        self._obj = obj
        self._rule = rule
        self._msg = msg if msg else f'{rule.__name__} не прошел проверку'
        self._exc = exc if exc else ValueError
    
    def _exec_func(self) -> bool:
        """Выполняет проверку по правилу."""
        return bool(self._rule(self._obj))


class BitwiseRule(Followable):
    """Побитовое правило для проверки объекта."""

    def __init__(
        self,
        rule: BitwiseRuleResult,
        msg: Optional[str] = None,
        exc: Optional[Exception] = None,
        obj: Any = None
    ):
        self._rule = rule
        self._exc = exc if exc else ValueError
        self._msg = msg if msg else f'{rule.__name__} не прошел проверку'
        self._obj = obj
    
    @property
    def obj(self):
        return self._obj
    
    @obj.setter
    def obj(self, obj: Any):
        self._obj = obj
    
    def follow(self) -> bool:
        """Проверяет соответствие правилу."""
        self._rule.obj = self.obj
        if not self._rule():
            raise self._exc(self._msg)

        return True