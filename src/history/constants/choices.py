from django.db.models import TextChoices


class HistoryTaskStatusChoices(TextChoices):
    SUCCESSFUL = 'SUCCESSFUL', 'Успешно выполнена вовремя'
    OUT_OF_DEADLINE = 'OUT_OF_DEADLINE', 'Выполнена с опозданием'
    FAILED = 'FAILED', 'Провалена'

