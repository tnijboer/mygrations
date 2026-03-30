from mygrations.core.parse.parser import Parser
from .type import Type


class TypePlain(Parser, Type):
    has_comma = False
    _is_primary_key = False

    # created date
    # The NULL / NOT NULL rules are repeated before and after DEFAULT to support
    # both orderings (`NOT NULL DEFAULT x` and `DEFAULT x NOT NULL`), following
    # the same pattern used by TypeCharacter and TypeText for repeated optional rules.
    rules = [
        {"type": "regexp", "value": "[^\(\s\)]+", "name": "name"},
        {"type": "regexp", "value": "\w+", "name": "type"},
        {"type": "literal", "value": "UNSIGNED", "optional": True},
        {"type": "literal", "value": "NULL", "optional": True, "name": "bare_null"},
        {"type": "literal", "value": "NOT NULL", "optional": True},
        {"type": "literal", "value": "PRIMARY KEY", "optional": True},
        {
            "type": "regexp",
            "value": "DEFAULT ([^\(\s\),]+)",
            "optional": True,
            "name": "default",
        },
        {"type": "literal", "value": "NULL", "optional": True, "name": "bare_null"},
        {"type": "literal", "value": "NOT NULL", "optional": True},
        {"type": "literal", "value": "PRIMARY KEY", "optional": True},
        {"type": "literal", "value": "AUTO_INCREMENT", "optional": True},
        {"type": "literal", "value": ",", "optional": True, "name": "ending_comma"},
    ]

    def process(self):

        self.has_comma = True if "ending_comma" in self._values else False

        self._parsing_errors = []
        self._parsing_warnings = []
        self._schema_errors = []
        self._schema_warnings = []
        self._name = self._values["name"].strip("`")
        self._length = ""
        self._column_type = self._values["type"]
        self._unsigned = True if "UNSIGNED" in self._values else False
        self._has_default = "default" in self._values
        self._default = self._values["default"].strip("'") if "default" in self._values else None
        self._auto_increment = True if "AUTO_INCREMENT" in self._values else False
        self._is_primary_key = True if "PRIMARY KEY" in self._values else False

        if "NOT NULL" in self._values:
            self._null = False
        else:
            self._null = True

        if self._column_type.upper() in ("BOOLEAN", "BOOL"):
            self._column_type = "TINYINT"
            self._length = "1"
            if self._default is not None and self._default.upper() == "FALSE":
                self._default = "0"
            elif self._default is not None and self._default.upper() == "TRUE":
                self._default = "1"

        # make sense of the default
        if self._default and self._default.lower() == "null":
            self._default = None
