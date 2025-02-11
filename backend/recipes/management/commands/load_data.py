import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные из CSV файла в модель Product'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к CSV файлу')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) != 2:
                    self.stdout.write(self.style.WARNING(
                        f'Пропущена некорректная строка: {row}')
                    )
                    continue
                name, measurement_unit = row
                try:
                    obj, created = Ingredient.objects.get_or_create(
                        name=name,
                        defaults={'measurement_unit': measurement_unit}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Добавлен объект: {name} ({measurement_unit})'
                        ))
                    else:
                        self.stdout.write(
                            self.style.NOTICE(
                                'Объект уже существует:',
                                f'{name} ({measurement_unit})'
                            ))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            'Ошибка при добавлении объекта',
                            f'{name} ({measurement_unit}): {e}'
                        ))
