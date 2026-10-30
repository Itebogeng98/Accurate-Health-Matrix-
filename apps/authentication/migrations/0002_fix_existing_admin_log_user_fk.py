from django.db import migrations


def retarget_admin_log_user_fk(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return

    table_name = 'django_admin_log'
    column_name = 'user_id'
    target_table = 'accounts_customuser'

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            """,
            [table_name, column_name],
        )
        constraints = cursor.fetchall()

        has_target_constraint = False
        for constraint_name, referenced_table in constraints:
            if referenced_table == target_table:
                has_target_constraint = True
                continue
            cursor.execute(f'ALTER TABLE `{table_name}` DROP FOREIGN KEY `{constraint_name}`')

        cursor.execute(f'ALTER TABLE `{table_name}` MODIFY `{column_name}` bigint NOT NULL')

        if has_target_constraint:
            return

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM django_admin_log log
            LEFT JOIN accounts_customuser user_model ON log.user_id = user_model.id
            WHERE log.user_id IS NOT NULL AND user_model.id IS NULL
            """
        )
        if cursor.fetchone()[0]:
            return

        cursor.execute(
            f"""
            ALTER TABLE `{table_name}`
            ADD CONSTRAINT `django_admin_log_user_id_custom_fk`
            FOREIGN KEY (`{column_name}`) REFERENCES `{target_table}` (`id`)
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(retarget_admin_log_user_fk, migrations.RunPython.noop),
    ]
