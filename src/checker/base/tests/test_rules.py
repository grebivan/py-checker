from typing import Any

import pytest

from ..rules import BitwiseRule
from ..rules import Rule
from ..rules import WrappedRule



class FixtureObj:
    """Фикстура для тестов."""
    def __init__(self, a: Any, b: Any = 'b'):
        self.a = a
        self.b = b


@pytest.fixture
def rule_obj():
    """Возвращает фикстуру для тестов."""
    return FixtureObj('a')


def test_rule(rule_obj):
    """Проверяет работу правила."""
    a_rule = Rule(attribute='a', func=lambda x: x == 'a', obj=rule_obj)
    a_rule.follow()


def test_rule_raise_default(rule_obj):
    """Проверяет вызов стандартного исключения при ошибке."""
    a_rule = Rule(attribute='a', func=lambda x: x == 'aa', obj=rule_obj)
    with pytest.raises(ValueError):
        a_rule.follow()

def test_rule_raise_default_exc_and_msg(rule_obj):
    """Проверяет вызов стандартного исключения при ошибке."""
    a_rule = Rule(attribute='a', func=lambda x: x == 'aa', obj=rule_obj)
    with pytest.raises(ValueError) as exc:
        a_rule.follow()
    
    assert "a не прошел проверку" == str(exc.value)


def test_rule_raise_default_exc_and_custom_msg(rule_obj):
    """Проверяет вызов стандартного исключения при ошибке."""
    exc_msg = "Пользовательская ошибка"
    a_rule = Rule(
        attribute='a',
        func=lambda x: x == 'aa',
        obj=rule_obj,
        msg=exc_msg)
    with pytest.raises(ValueError) as exc:
        a_rule.follow()
    
    assert exc_msg == str(exc.value)


def test_rule_raise_custom(rule_obj):
    """Проверяет вызов пользовательского исключения при ошибке."""
    a_rule = Rule(
        attribute='a',
        func=lambda x: x == 'aa',
        obj=rule_obj,
        exc=TypeError
    )
    with pytest.raises(TypeError):
        a_rule.follow()


def test_wrapped_rule(rule_obj):
    """Проверяет работу callable правил."""
    rule = WrappedRule(rule=lambda x: x.a == 'a', obj=rule_obj)
    rule.follow()


def test_wrapped_rule_raise_default(rule_obj):
    """Проверяет работу callable правил."""
    rule = WrappedRule(rule=lambda x: x.a == 'aa', obj=rule_obj)
    with pytest.raises(ValueError):
        rule.follow()


def test_bitwise_rules_with_obj(rule_obj):
    """Проверяет работу бинарных правил с объектом."""
    rule = BitwiseRule(
        Rule(attribute='a', func=lambda x: x == 'a') &
        Rule(attribute='b', func=lambda x: x == 'b'),
        obj=rule_obj
    )
    rule.follow()


def test_bitwise_rules_without_obj(rule_obj):
    """Проверяет работу бинарных правил без объекта."""
    rule = BitwiseRule(
        Rule(attribute='a', func=lambda x: x == 'a', obj=rule_obj) &
        Rule(attribute='b', func=lambda x: x == 'b', obj=rule_obj),
    )
    rule.follow()


def test_bitwise_rules_with_wrapped(rule_obj):
    """Проверяет работу бинарных правил с callable правилом."""
    rule = BitwiseRule(
        WrappedRule(rule=lambda x: x.a == 'a') &
        Rule(attribute='b', func=lambda x: x == 'b'),
        obj=rule_obj
    )
    rule.follow()


def test_bitwise_rules_with_wrapped_or(rule_obj):
    """Проверяет работу бинарных правил с ``or``."""
    rule = BitwiseRule(
        WrappedRule(rule=lambda x: x.a == 'a') |
        Rule(attribute='b', func=lambda x: x == 'bb'),
        obj=rule_obj
    )
    rule.follow()


def test_bitwise_rules_raises_default(rule_obj):
    """Проверяет вызов стандартного исключения при ошибке"""
    rule = BitwiseRule(
        WrappedRule(rule=lambda x: x.a == 'a') &
        Rule(attribute='b', func=lambda x: x == 'bb'),
        obj=rule_obj
    )
    with pytest.raises(ValueError):
        rule.follow()


def test_bitwise_rules_raises_custom(rule_obj):
    """Проверяет вызов пользовательского исключения при ошибке."""
    rule = BitwiseRule(
        WrappedRule(rule=lambda x: x.a == 'a') &
        Rule(attribute='b', func=lambda x: x == 'bb'),
        obj=rule_obj,
        exc=TypeError
    )
    with pytest.raises(TypeError):
        rule.follow()
