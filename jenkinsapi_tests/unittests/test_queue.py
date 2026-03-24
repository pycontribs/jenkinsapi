import mock
import pytest

from jenkinsapi.queue import Queue


@pytest.fixture
def queue(monkeypatch):
    def fake_poll(self, tree=None):  # pylint: disable=unused-argument
        return {
            "items": [
                {
                    "id": 1,
                    "task": {
                        "name": "folder1/folder2/job-name",
                        "url": "http://localhost:8080/job/folder1/job/folder2/job/job-name/",
                    },
                }
            ]
        }

    monkeypatch.setattr(Queue, "_poll", fake_poll)
    return Queue("http://localhost:8080/queue", mock.MagicMock())


def test_queue_items_for_job_normalizes_path(queue):
    items = queue.get_queue_items_for_job("folder1/folder2/job-name")

    assert len(items) == 1
