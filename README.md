# Пакет для декларативного описания проверок объекта

Если в проекте есть большоое количество последовательных проверок объекта, например:

```python

class SomeClass:
    ...
    def _first_check(self, first_obj):
        if not first_obj.attribute:
            raise AppliсationException('attribute')
        if not first_obj.another_attribute:
            raise AppliсationException('another_attribute')
        if not first_obj.some_attribute:
            raise AppliсationException('some_attribute')
        # еще аналогичные if выражения
 
    def _second_check(self, second_obj):
        if not second_obj.attribute:
            raise AppliсationException('attribute')
        if not second_obj.another_attribute:
            raise AppliсationException('another_attribute')
        if not second_obj.some_attribute:
            raise AppliсationException('some_attribute')
        # еще аналогичные if выражения
 
    # еще аналогичные методы для проверок
 
    def check(self):
        self._first_check(self.obj.first_obj)
        self._second_check(self.obj.second_obj)
        # вызов остальных методов для проверок
 
    def run(self):
        self.check()
        self.do_somthing()

```

То с помощью этого пакета описание правил и их проверку можно вынести в отдельный класс:

```python

# checkers.py
 
class EmployeeChecker(BaseChecker):
    """Набор правил для записи о Сотруднике."""
 
    last_name = Rule(attribute='last_name', func=bool, msg='Не задано отчество')
    complex_rule = BitwiseRule(
        WrappedRule(rule=lambda employee: employee.job_set.exists()) and
        Rule(attribute='date_to', func=operator.not_),
        exc=TypeError,
        msg='Не выполнено комплексное условие проверки.'
    )
 
 
# services.py
 
from .checkers import EmployeeChecker
 
 
class SyncEmployee:
    """Класс для синхронизации сотрудника с внешней системой."""
 
    checker = EmployeeChecker
 
    ...
 
    def run(self):
        checker = self.checker(self.employee)
        checker.check()
        self.sync()

```

Для группировки Правил в Проверку требуется создать класс-наследник от BaseChecker . В созданном классе в качестве атрибутов класса перечислить набор Правил. Как видно из примера, Правила могут быть:

Простыми:

* Rule - при инициализации указывается атрибут проверяемого объекта и функция для проверки значения этого атрибута. Атрибут msg является необязательным.
* WrappedRule  - при инициализации указывается функция для проверки. При обработке данного Правила проверяемый объект автоматически будет передан в Правило.

Составными:

* BitwiseRule  - как следует из названия, ожидает что в качестве обязательного аргумента будет передан результат побитовой операции между простыми Правилами. Поддерживаются AND  и OR  выражения.

Для всех видов Правил есть возможно задавать Исключение и Сообщение, которое будет вызвано в случае не соблюдения условия проверки.

В примере использования(блок `services.py` ) демонстрируется применение реализованной Проверки. При инстанцировании проверки требуется передать в качестве аргумента проверяемый объект(`self.employee`). Для запуска проверок требуется вызвать метод `.check()`.
