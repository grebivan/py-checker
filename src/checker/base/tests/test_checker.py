from typing import Any

import pytest

# from checker.base.checker import BaseChecker
# from checker.base.rules import BitwiseRule
# from checker.base.rules import Rule
# from checker.base.rules import WrappedRule

from ..checker import BaseChecker
from ..rules import BitwiseRule
from ..rules import Rule
from ..rules import WrappedRule



class Checker(BaseChecker):
    """Проверка для тестирования."""

    a = Rule(attribute='a', func=lambda x: x == 'a')
    b = BitwiseRule(
        WrappedRule(rule=lambda x: x.a == 'a') &
        Rule(attribute='b', func=lambda x: x == 'b')
    )


class FixtureObj:
    """Фикстура для тестов."""
    def __init__(self, a: Any, b: Any ='b'):
        self.a = a
        self.b = b


@pytest.fixture
def rule_obj():
    return FixtureObj('a')


def test_checker(rule_obj):
    """Проверяет выполнение правил в проверке."""
    checker = Checker(rule_obj)
    checker.check()


def test_checker_raises(rule_obj):
    """Проверяет вызов исключения при ошибке проверки."""
    rule_obj.b = 'bb'
    checker = Checker(rule_obj)
    with pytest.raises(ValueError):
        checker.check()
