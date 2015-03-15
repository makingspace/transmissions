from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import DatabaseError


class Command(BaseCommand):
    help = 'Rename app from django_transmissions to transmissions'
    option_list = BaseCommand.option_list
    args = ""

    def handle(self, db_dry_run=False, *args, **options):

        message = "Updating django_content_type app_label"
        sql = "UPDATE django_content_type SET app_label='transmissions' WHERE app_label='django_transmissions'"
        self.execute_sql(sql, message)

        message = "Rename django_transmissions_trigger"
        sql = "ALTER TABLE django_transmissions_trigger RENAME TO transmissions_trigger"
        self.execute_sql(sql, message)

        message = "Rename django_transmissions_notification"
        sql = "ALTER TABLE django_transmissions_notification RENAME TO transmissions_notification"
        self.execute_sql(sql, message)

    def execute_sql(self, sql, message):

        cursor = connection.cursor()

        self.stdout.write("Rename django_transmissions_notification... ", ending='')
        try:
            cursor.execute(sql)
            self.stdout.write('{}... SUCCEEDED'.format(message))
        except DatabaseError:
            self.stderr.write('{}... FAILED'.format(message))