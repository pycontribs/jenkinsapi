"""
Tests for issue #780: Cannot parse response.content when contains null as value.

Jenkins responses can contain JSON null values which json.loads() handles correctly.
"""

import json


def test_json_with_null_values_parses_correctly():
    """json.loads() correctly parses JSON responses with null values."""
    json_with_null = """{
        "id": "953",
        "name": "#953",
        "status": "ABORTED",
        "message": null,
        "stages": [
            {
                "id": "361",
                "name": "Stage 1",
                "status": "FAILED",
                "error": {
                    "message": null,
                    "type": "FlowInterruptedException"
                }
            }
        ]
    }"""

    # Should not raise an exception
    data = json.loads(json_with_null)

    assert data["id"] == "953"
    assert data["message"] is None
    assert data["stages"][0]["error"]["message"] is None


def test_json_with_deeply_nested_null():
    """Deeply nested null values are parsed correctly."""
    json_data = """{
        "level1": {
            "level2": {
                "level3": null,
                "level3b": "value"
            },
            "level2b": null
        },
        "list": [null, "item", null]
    }"""

    data = json.loads(json_data)

    assert data["level1"]["level2"]["level3"] is None
    assert data["level1"]["level2"]["level3b"] == "value"
    assert data["level1"]["level2b"] is None
    assert data["list"][0] is None
    assert data["list"][1] == "item"
    assert data["list"][2] is None


def test_json_loads_handles_normal_responses():
    """Ensure json.loads() doesn't break normal JSON parsing."""
    json_data = """{
        "jobs": [
            {"name": "job1", "color": "blue"},
            {"name": "job2", "color": "red"}
        ],
        "views": [
            {"name": "All", "url": "http://dummy/"}
        ]
    }"""

    data = json.loads(json_data)

    assert len(data["jobs"]) == 2
    assert data["jobs"][0]["name"] == "job1"
    assert len(data["views"]) == 1
