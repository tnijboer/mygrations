import unittest

from mygrations.formats.mysql.file_reader.database import Database as DatabaseReader
from mygrations.formats.mysql.mygrations.mygration import Mygration


class test_fk_column_type_change(unittest.TestCase):
    parent_table_signed = """CREATE TABLE `businesses` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

    parent_table_unsigned = """CREATE TABLE `businesses` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

    child_table_signed = """CREATE TABLE `company_domains` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`business_id` INT(10) NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

    child_table_unsigned = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

    def test_signed_to_unsigned_drops_and_readds_fk(self):
        """Changing INT to INT UNSIGNED on FK columns should DROP FK before ALTER and ADD FK after"""
        db_from = DatabaseReader([self.parent_table_signed, self.child_table_signed])
        db_to = DatabaseReader([self.parent_table_unsigned, self.child_table_unsigned])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        self.assertEqual("SET FOREIGN_KEY_CHECKS=0;", ops[0])
        self.assertIn("DROP FOREIGN KEY `company_domains_business_id_fk`", ops[1])
        self.assertTrue(any("CHANGE" in op for op in ops), "Expected a CHANGE column operation")
        self.assertIn(
            "ADD CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE",
            ops[-2],
        )
        self.assertEqual("SET FOREIGN_KEY_CHECKS=1;", ops[-1])

    def test_no_fk_cycle_when_types_match(self):
        """No extra DROP/ADD FK when column types are already the same"""
        db_from = DatabaseReader([self.parent_table_unsigned, self.child_table_unsigned])
        db_to = DatabaseReader([self.parent_table_unsigned, self.child_table_unsigned])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        all_ops_str = " ".join(ops)
        self.assertNotIn("DROP FOREIGN KEY", all_ops_str)
        self.assertNotIn("ADD CONSTRAINT", all_ops_str)

    def test_parent_type_change_cycles_child_fk(self):
        """Changing the parent column type should also cycle the child's FK"""
        parent_signed = """CREATE TABLE `businesses` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        parent_unsigned = """CREATE TABLE `businesses` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child_unsigned = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        db_from = DatabaseReader([parent_signed, child_unsigned])
        db_to = DatabaseReader([parent_unsigned, child_unsigned])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        self.assertEqual("SET FOREIGN_KEY_CHECKS=0;", ops[0])
        self.assertIn("DROP FOREIGN KEY `company_domains_business_id_fk`", ops[1])
        self.assertTrue(any("CHANGE" in op or "MODIFY" in op for op in ops))
        self.assertIn(
            "ADD CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE",
            ops[-2],
        )
        self.assertEqual("SET FOREIGN_KEY_CHECKS=1;", ops[-1])

    def test_fk_definition_change_with_type_change_no_duplicates(self):
        """When both FK definition and column type change, no duplicate DROP/ADD FK"""
        parent_signed = """CREATE TABLE `businesses` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        parent_unsigned = """CREATE TABLE `businesses` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child_signed_cascade = """CREATE TABLE `company_domains` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`business_id` INT(10) NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child_unsigned_restrict = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        db_from = DatabaseReader([parent_signed, child_signed_cascade])
        db_to = DatabaseReader([parent_unsigned, child_unsigned_restrict])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        drop_fk_count = sum(1 for op in ops if "DROP FOREIGN KEY `company_domains_business_id_fk`" in op)
        add_fk_count = sum(1 for op in ops if "ADD CONSTRAINT `company_domains_business_id_fk`" in op)

        self.assertEqual(1, drop_fk_count, f"Expected exactly 1 DROP FK, got {drop_fk_count}. Operations: {ops}")
        self.assertEqual(1, add_fk_count, f"Expected exactly 1 ADD FK, got {add_fk_count}. Operations: {ops}")
        self.assertIn("ON DELETE RESTRICT", ops[-2])

    def test_multiple_fks_on_same_parent(self):
        """Multiple child tables referencing the same parent column that changes type"""
        parent_signed = """CREATE TABLE `businesses` (`id` INT(10) NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        parent_unsigned = """CREATE TABLE `businesses` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child1 = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `bd_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child2 = """CREATE TABLE `company_users` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`user_name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `bu_business_id_idx` (`business_id`),
CONSTRAINT `bu_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        db_from = DatabaseReader([parent_signed, child1, child2])
        db_to = DatabaseReader([parent_unsigned, child1, child2])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        all_ops_str = " ".join(ops)
        self.assertIn("DROP FOREIGN KEY `bd_business_id_fk`", all_ops_str)
        self.assertIn("DROP FOREIGN KEY `bu_business_id_fk`", all_ops_str)
        self.assertIn("ADD CONSTRAINT `bd_business_id_fk`", all_ops_str)
        self.assertIn("ADD CONSTRAINT `bu_business_id_fk`", all_ops_str)

    def test_unrelated_column_change_no_fk_cycle(self):
        """Changing a non-FK column should NOT trigger FK cycling"""
        parent = """CREATE TABLE `businesses` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`name` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child_before = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(255) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        child_after = """CREATE TABLE `company_domains` (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
`business_id` INT(10) UNSIGNED NOT NULL,
`domain` VARCHAR(512) NOT NULL DEFAULT '',
PRIMARY KEY (`id`),
KEY `business_id_idx` (`business_id`),
CONSTRAINT `company_domains_business_id_fk` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        db_from = DatabaseReader([parent, child_before])
        db_to = DatabaseReader([parent, child_after])

        mygrate = Mygration(db_to, db_from)
        ops = [str(op) for op in mygrate.operations]

        all_ops_str = " ".join(ops)
        self.assertNotIn("DROP FOREIGN KEY", all_ops_str)
        self.assertNotIn("ADD CONSTRAINT", all_ops_str)
        self.assertTrue(any("CHANGE" in op for op in ops))
