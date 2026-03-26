import unittest

from mygrations.formats.mysql.file_reader.create_parser import CreateParser


class CreateParserTest(unittest.TestCase):
    def test_complicated_table_parses(self):

        # parse a typical foreign key constraint
        parser = CreateParser()
        returned = parser.parse(
            """CREATE TABLE `tasks` (
            `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
            `account_id` int(10) DEFAULT NULL,
            `membership_id` int(10) DEFAULT NULL,
            `status_id` int(10) DEFAULT NULL,
            `priority_id` int(10) unsigned DEFAULT NULL,
            `task_type_id` int(10) unsigned DEFAULT NULL,
            `task_team_id` int(10) unsigned DEFAULT NULL,
            `repeating_tasks_id` int(10) unsigned DEFAULT NULL,
            `subject` varchar(255) DEFAULT NULL,
            `task` varchar(255) DEFAULT NULL,
            `due_date` int(10) DEFAULT NULL,
            `original_due_date` int(10) DEFAULT NULL,
            `assigned_to_id` int(10) unsigned DEFAULT NULL,
            `delegated_to_id` int(10) DEFAULT NULL,
            `trust` tinyint(1) NOT NULL DEFAULT 0,
            `description` text,
            `multiple_task_id` int(10) DEFAULT NULL,
            `completed_dt` int(10) DEFAULT NULL,
            `duration` int(10) NOT NULL DEFAULT 0,
            `number_comments` int(10) NOT NULL DEFAULT 0,
            `number_uploads` int(10) NOT NULL DEFAULT '0',
            `created` int(10) DEFAULT NULL,
            `updated` int(10) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `task_status_id` (`status_id`),
            KEY `task_priority_id` (`priority_id`),
            KEY `tasks_membership_id` (`membership_id`),
            KEY `task_type_id` (`task_type_id`),
            KEY `task_assigned_to_id` (`assigned_to_id`),
            CONSTRAINT `tasks_assigned_to_id_ref_memberships_user_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `memberships` (`id`) ON DELETE SET NULL,
            CONSTRAINT `tasks_priority_id_ref_task_priorities_id` FOREIGN KEY (`priority_id`) REFERENCES `task_priorities` (`id`) ON UPDATE CASCADE,
            CONSTRAINT `tasks_type_id_ref_task_types_id` FOREIGN KEY (`task_type_id`) REFERENCES `task_types` (`id`) ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
        )

        # we should have matched
        self.assertTrue(parser.matched)

        # and we should have matched everything
        self.assertEqual("tasks", parser.name)
        self.assertEqual("", returned)
        self.assertEqual(23, len(parser.columns))
        self.assertEqual(6, len(parser.indexes))
        self.assertEqual(3, len(parser.constraints))
        self.assertEqual(2, len(parser.options))
        self.assertTrue(parser.semicolon)
        self.assertEqual(0, len(parser.schema_errors))
        self.assertEqual(["id"], parser.primary.columns)

    def test_keeps_errors(self):

        # parse a typical foreign key constraint
        parser = CreateParser()
        returned = parser.parse(
            """CREATE TABLE `tasks` (
            `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
            `subject` varchar DEFAULT NULL,
            `task` text DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
        )

        # we should have matched
        self.assertTrue(parser.matched)

        # and we should have some errors
        self.assertEqual(2, len(parser.schema_errors))
        self.assertEqual(
            "Column 'task' of type 'TEXT' cannot have a default in table 'tasks'",
            parser.schema_errors[0],
        )
        self.assertEqual(
            "Table 'tasks' has an AUTO_INCREMENT column but is missing the PRIMARY index",
            parser.schema_errors[1],
        )

    def test_if_not_exists_parses(self):

        # parse CREATE TABLE IF NOT EXISTS with a complicated table
        parser = CreateParser()
        returned = parser.parse(
            """CREATE TABLE IF NOT EXISTS `tasks` (
            `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
            `account_id` int(10) DEFAULT NULL,
            `membership_id` int(10) DEFAULT NULL,
            `status_id` int(10) DEFAULT NULL,
            `priority_id` int(10) unsigned DEFAULT NULL,
            `task_type_id` int(10) unsigned DEFAULT NULL,
            `task_team_id` int(10) unsigned DEFAULT NULL,
            `repeating_tasks_id` int(10) unsigned DEFAULT NULL,
            `subject` varchar(255) DEFAULT NULL,
            `task` varchar(255) DEFAULT NULL,
            `due_date` int(10) DEFAULT NULL,
            `original_due_date` int(10) DEFAULT NULL,
            `assigned_to_id` int(10) unsigned DEFAULT NULL,
            `delegated_to_id` int(10) DEFAULT NULL,
            `trust` tinyint(1) NOT NULL DEFAULT 0,
            `description` text,
            `multiple_task_id` int(10) DEFAULT NULL,
            `completed_dt` int(10) DEFAULT NULL,
            `duration` int(10) NOT NULL DEFAULT 0,
            `number_comments` int(10) NOT NULL DEFAULT 0,
            `number_uploads` int(10) NOT NULL DEFAULT '0',
            `created` int(10) DEFAULT NULL,
            `updated` int(10) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `task_status_id` (`status_id`),
            KEY `task_priority_id` (`priority_id`),
            KEY `tasks_membership_id` (`membership_id`),
            KEY `task_type_id` (`task_type_id`),
            KEY `task_assigned_to_id` (`assigned_to_id`),
            CONSTRAINT `tasks_assigned_to_id_ref_memberships_user_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `memberships` (`id`) ON DELETE SET NULL,
            CONSTRAINT `tasks_priority_id_ref_task_priorities_id` FOREIGN KEY (`priority_id`) REFERENCES `task_priorities` (`id`) ON UPDATE CASCADE,
            CONSTRAINT `tasks_type_id_ref_task_types_id` FOREIGN KEY (`task_type_id`) REFERENCES `task_types` (`id`) ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
        )

        # we should have matched
        self.assertTrue(parser.matched)

        # and we should have matched everything (table name should be 'tasks', not 'IF')
        self.assertEqual("tasks", parser.name)
        self.assertEqual("", returned)
        self.assertEqual(23, len(parser.columns))
        self.assertEqual(6, len(parser.indexes))
        self.assertEqual(3, len(parser.constraints))
        self.assertEqual(2, len(parser.options))
        self.assertTrue(parser.semicolon)
        self.assertEqual(0, len(parser.schema_errors))
        self.assertEqual(["id"], parser.primary.columns)
