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
        BitwiseRule(a_rule & b_rule)
    ),
)
checker.check()
print('OK')

test.b = None
checker = Checker(
    obj=test,
    rules=(
        a_rule,
        BitwiseRule(a_rule | b_rule)
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
        WrappedRule(rule=chek_test1),
        BitwiseRule(WrappedRule(rule=chek_test, msg='Бяда1!') | a_rule, msg='Бяда!'),
    ),
)
checker.check()


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


class TestChecker(BaseChecker):
    a_rule = Rule(attribute='a', func=lambda x: x=='a')
    b_rule = BitwiseRule(
        Rule(attribute='b', func=lambda x: x=='b') | a_rule
    )

test_ch = TestChecker(test)
test_ch.check()