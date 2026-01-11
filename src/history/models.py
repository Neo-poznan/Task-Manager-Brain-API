from django.db import models
from django.contrib.auth import get_user_model

from task.models import DomainQuerySet
from .domain import HistoryEntity, SharedHistoryEntity
from .constants.choices import HistoryTaskStatusChoices


class History(models.Model):


    class Meta:
        verbose_name = '''
            История выполненных и проваленных задач. Одна строка - одна задача.
        '''


    name = models.CharField(
            max_length=290, 
            null=False, 
            blank=False, 
            verbose_name='Название задачи'
        )
    category = models.ForeignKey(
            to='task.Category',
            on_delete=models.SET_NULL,
            null=True, 
            blank=True, 
            verbose_name='Категория задачи'
        )
    user = models.ForeignKey(
            to=get_user_model(), 
            on_delete=models.CASCADE, 
            null=False, 
            blank=False, 
            verbose_name='Пользователь, создавший задачу'
        )
    planned_time = models.DurationField(
            null=False, 
            blank=False, 
            verbose_name='Время, которое было изначально запланировано на процесс выполнения задачи'
        )
    execution_time = models.DurationField(
            null=False, 
            blank=False, 
            verbose_name='Время, которое реально потребовалось на выполнение задачи'
        )
    execution_date = models.DateField(
            null=False, 
            blank=False, 
            auto_now_add=True, 
            verbose_name='День, в который была выполнена задача'
        )
    status = models.CharField(
            max_length=50, 
            null=False,
            blank=False, 
            choices=HistoryTaskStatusChoices.choices, 
            verbose_name='Статус, к примеру, была задача выполнена или провалена'
        )

    objects = DomainQuerySet.as_manager()

    @classmethod
    def from_domain(cls, entity: HistoryEntity):
        return cls(
            id=entity.id,
            name=entity.name,
            user_id=entity.user_id,
            category_id=entity.category_id,
            planned_time=entity.planned_time,
            execution_time=entity.execution_time,
            execution_date=entity.execution_date,
            status=entity.status
        )

    def to_domain(self) -> HistoryEntity:
        return HistoryEntity(
            id=self.id,
            name=self.name,
            user_id=self.user.id,
            category_id=self.category.id if self.category else None,
            planned_time=self.planned_time,
            execution_time=self.execution_time,
            execution_date=self.execution_date,
            status=self.status
        )

    def __str__(self):
        return self.name + ' ' + self.category.name


class SharedHistory(models.Model):


    class Meta:
        verbose_name = '''
        Закэшированная в базе данных история пользователя по определенному отрезку времени,
        чтобы сохранить ее в быстром доступе и поделиться с другими пользователями
        '''

    
    key = models.CharField(
            max_length=13, 
            primary_key=True, 
            verbose_name='Уникальный ключ по которому можно получить историю'
        )
    user = models.ForeignKey(
            to=get_user_model(), 
            on_delete=models.CASCADE, 
            null=False, 
            blank=False, 
            verbose_name='Пользователь, сохранивший статистику'
        )
    from_date = models.DateField(
            verbose_name='Дата, начиная с которой будет показана история',
            null=True
        )
    to_date = models.DateField(
            verbose_name='Крайняя дата, по которую будет показана показана история', 
            null=True
        )
    history_statistics = models.JSONField(
            verbose_name='Сохраненная история пользователя по определенному промежутку времени'
        )

    objects = DomainQuerySet.as_manager()


    @classmethod
    def from_domain(cls, entity: SharedHistoryEntity):
        return cls(
            key=entity.key,
            user_id=entity.user_id,
            from_date=entity.from_date,
            to_date=entity.to_date,
            history_statistics=entity.history_statistics
        )

    def to_domain(self):
        return SharedHistoryEntity(
            key=self.key,
            user_id=self.user.id,
            from_date=self.from_date,
            to_date=self.to_date,
            history_statistics=self.history_statistics
        )

