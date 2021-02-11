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


def lazy_exec_args(func: Callable, *args):
    """Выполняет функцию с callable аргументами."""
    return func(
        *map(lambda f: f() if callable(f) else f, args)
    )


def wrapped_partial(func: Callable, *args, **kwargs):
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
        self._func = wrapped_partial(func, *args)
    
    def __call__(self) -> Any:
        return self._func()
    
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
    """Обертка для применения не `Rule` в `ComplexRule`."""
    def __init__(
        self,
        func: Callable,
        msg: str,
        exc: Optional[Exception] = None,
        obj: Any = None,
    ):
        self._obj = obj
        self._func = func
        self._msg = msg
        self._exc = exc if exc else ValueError
    
    def _exec_func(self) -> bool:
        """Выполняет проверку по правилу."""
        return bool(self._func(self._obj))


class ComplexRule(Followable):
    """Состаное правило для проверки объекта."""

    def __init__(
        self,
        rule: Callable,
        msg: str,
        exc: Optional[Exception] = None,
    ):
        self._rule = rule
        self._exc = exc if exc else ValueError
        self._msg = msg if msg else f'{rule.__name__} не прошел проверку'
    
    def follow(self) -> bool:
        """Проверяет соответствие правилу."""
        if not self._rule():
            raise self._exc(self._msg)

        return True


class Checker:
    """Проверка объекта по набору правил."""

    def __init__(
        self,
        obj: Any,
        rules: Sequence[Followable]
    ):
        self._obj = obj
        self._rules = rules
    
    def check(self):
        """Выполняет проверку объекта по указанным правилам."""
        for rule in self._rules:
            if hasattr(rule, "obj"):
                rule.obj = self._obj
            
            rule.follow()

class Test:
    def __init__(self, a = None, b = None, c = None):
        self.a = a
        self.b = b
        self.c = c


class TestNested:
    def __init__(self, n = None):
        self.n = n
    
    def nested(self):
        return self.n


test = Test('a', 'b', TestNested('c'))
a_rule = Rule(attribute='a', func=lambda x: x=='a')
b_rule = Rule(attribute='b', func=lambda x: x=='b')
c_rule = Rule(attribute='c.nested', func=lambda x: x=='c')
checker = Checker(
    obj=test,
    rules=(
        a_rule,
        b_rule,
        c_rule,
        ComplexRule(a_rule & b_rule, msg='Внимание!')
    ),
)
checker.check()
print('OK')

test.b = None
checker = Checker(
    obj=test,
    rules=(
        a_rule,
        ComplexRule(a_rule & b_rule | c_rule, msg='Внимание!!!')
    ),
)
checker.check()

def chek_test(obj):
    return obj.b == 3

def chek_test1(obj):
    return obj.a == 'a'

checker = Checker(
    obj=test,
    rules=(
        a_rule,
        WrappedRule(func=chek_test1, msg='Бяда1 !'),
        ComplexRule(WrappedRule(func=chek_test, msg='Бяда!', obj=test) | a_rule, msg='Бяда!'),
    ),
)
checker.check()