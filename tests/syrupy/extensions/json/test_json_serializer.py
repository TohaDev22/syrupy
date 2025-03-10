from collections import (
    OrderedDict,
    namedtuple,
)

import pytest

from syrupy.extensions.amber.serializer import AmberDataSerializer
from syrupy.extensions.json import JSONSnapshotExtension


@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


def test_non_snapshots(snapshot_json):
    with pytest.raises(AssertionError):
        assert "Lorem ipsum." == "Muspi merol."


def test_reflection(snapshot_json):
    assert snapshot_json == snapshot_json


def test_empty_snapshot(snapshot_json):
    assert snapshot_json == None  # noqa: E711
    assert snapshot_json == ""


def test_snapshot_markers(snapshot_json):
    """
    Test snapshot markers do not break serialization when in snapshot data
    """
    marker_strings = (
        AmberDataSerializer._marker_prefix,
        f"{AmberDataSerializer._indent}{AmberDataSerializer._marker_prefix}",
        f"{AmberDataSerializer._marker_prefix}{AmberDataSerializer.Marker.Divider}",
        f"{AmberDataSerializer._marker_prefix}{AmberDataSerializer.Marker.Name}:",
    )
    assert snapshot_json == "\n".join(marker_strings)


def test_newline_control_characters(snapshot_json):
    assert snapshot_json == "line 1\nline 2"
    assert snapshot_json == "line 1\r\nline 2"
    assert snapshot_json == "line 1\r\nline 2\r\n"
    assert snapshot_json == "line 1\rline 2\r"
    assert snapshot_json == "line 1\rline 2\n"
    assert snapshot_json == "line 1\rline 2"


def test_multiline_string_in_dict(snapshot_json):
    lines = "\n".join(["line 1", "line 2"])
    assert {"value": lines} == snapshot_json


def test_deeply_nested_multiline_string_in_dict(snapshot_json):
    lines = "\n".join(["line 1", "line 2", "line 3"])
    d = {"value_a": {"value_b": lines}}
    assert d == snapshot_json


@pytest.mark.parametrize("actual", [False, True])
def test_bool(actual, snapshot_json):
    assert actual == snapshot_json


@pytest.mark.parametrize(
    "actual",
    [
        "",
        r"Raw string",
        r"Escaped \n",
        r"Backslash \u U",
        "🥞🐍🍯",
        "singleline:",
        "- singleline",
        "multi-line\nline 2\nline 3",
        "multi-line\nline 2\n  line 3",
        "string with 'quotes'",
        b"Byte string",
    ],
    ids=lambda x: "",
)
def test_string(snapshot_json, actual):
    assert snapshot_json == actual


def test_multiple_snapshots(snapshot_json):
    assert "First." == snapshot_json
    snapshot_json.assert_match("Second.")
    assert snapshot_json == "Third."


ExampleTuple = namedtuple("ExampleTuple", ["a", "b", "c", "d"])


def test_tuple(snapshot_json):
    assert snapshot_json == ("this", "is", ("a", "tuple"))
    assert snapshot_json == ExampleTuple(a="this", b="is", c="a", d={"named", "tuple"})
    assert snapshot_json == ()


@pytest.mark.parametrize(
    "actual",
    [
        {"this", "is", "a", "set"},
        {"contains", "frozen", frozenset({"1", "2"})},
        {"contains", "tuple", (1, 2)},
        {"contains", "namedtuple", ExampleTuple(a=1, b=2, c=3, d=4)},
        set(),
    ],
)
def test_set(snapshot_json, actual):
    assert snapshot_json == actual


@pytest.mark.parametrize(
    "actual",
    [
        {"b": True, "c": "Some text.", "d": ["1", 2], "a": {"e": False}},
        {"b": True, "c": "Some ttext.", "d": ["1", 2], "a": {"e": False}},
        {
            1: True,
            "a": "Some ttext.",
            "multi\nline\nkey": "Some morre text.",
            frozenset({"1", "2"}): ["1", 2],
            ExampleTuple(a=1, b=2, c=3, d=4): {"e": False},
            "key": None,
        },
        {},
        {"key": ["line1\nline2"]},
        {"key": [1, "line1\nline2", 2, "line3\nline4"]},
        {"key": [1, ["line1\nline2"], 2]},
    ],
)
def test_dict(snapshot_json, actual):
    assert actual == snapshot_json


def test_numbers(snapshot_json):
    assert snapshot_json == 3.5
    assert snapshot_json == 7
    assert snapshot_json == 2 / 6


@pytest.mark.parametrize(
    "actual",
    [
        [],
        ["this", "is", "a", "list"],
        ["contains", "empty", []],
        [1, 2, "string", {"key": "value"}],
    ],
)
def test_list(snapshot_json, actual):
    assert actual == snapshot_json


list_cycle = [1, 2, 3]
list_cycle.append(list_cycle)

dict_cycle = {"a": 1, "b": 2, "c": 3}
dict_cycle.update(d=dict_cycle)


@pytest.mark.parametrize("cyclic", [list_cycle, dict_cycle])
def test_cycle(cyclic, snapshot_json):
    assert cyclic == snapshot_json


class CustomClass:
    a = 1
    b = "2"
    c = list_cycle
    d = dict_cycle
    _protected_variable = None
    __private_variable = None

    def __init__(self, x=None):
        self.x = x
        self._y = 1
        self.__z = 2

    def public_method(self, a, b=1, *, c, d=None):
        pass

    def _protected_method(self):
        pass

    def __private_method(self):
        pass


def test_custom_object_repr(snapshot_json):
    assert CustomClass(CustomClass()) == snapshot_json


class TestClass:
    def test_class_method_name(self, snapshot_json):
        assert snapshot_json == "this is in a test class"

    @pytest.mark.parametrize("actual", ["a", "b", "c"])
    def test_class_method_parametrized(self, snapshot_json, actual):
        assert snapshot_json == actual

    @pytest.mark.parametrize("actual", ["x", "y", "z"])
    class TestNestedClass:
        def test_nested_class_method(self, snapshot_json, actual):
            assert snapshot_json == f"parameterized nested class method {actual}"


class TestSubClass(TestClass):
    pass


@pytest.mark.parametrize("parameter_with_dot", ("value.with.dot",))
def test_parameter_with_dot(parameter_with_dot, snapshot_json):
    assert parameter_with_dot == snapshot_json


@pytest.mark.parametrize("parameter_1", ("foo",))
@pytest.mark.parametrize("parameter_2", ("bar",))
def test_doubly_parametrized(parameter_1, parameter_2, snapshot_json):
    assert parameter_1 == snapshot_json
    assert parameter_2 == snapshot_json


def test_ordered_dict(snapshot_json):
    d = OrderedDict()
    d["b"] = 0
    d["a"] = OrderedDict(b=True, a=False)
    assert snapshot_json == d
