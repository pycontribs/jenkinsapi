import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from jenkinsapi.command_line.jenkins_invoke import JenkinsInvoke


def test_main_requires_at_least_one_job(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["jenkins_invoke"])

    with pytest.raises(SystemExit) as exc:
        JenkinsInvoke.main()

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "the following arguments are required: job" in captured.err


def test_help_text_is_actionable(capsys):
    parser = JenkinsInvoke.mkparser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "Execute one or more Jenkins jobs" in output
    assert "One or more Jenkins job names to invoke." in output


def test_parser_uses_environment_defaults(monkeypatch):
    monkeypatch.setenv("JENKINS_URL", "https://jenkins.example")
    monkeypatch.setenv("JENKINS_USERNAME", "env-user")
    monkeypatch.setenv("JENKINS_API_TOKEN", "env-token")

    parser = JenkinsInvoke.mkparser()
    options = parser.parse_args(["job-one"])

    assert options.baseurl == "https://jenkins.example"
    assert options.username == "env-user"
    assert options.password == "env-token"


def test_resolve_password_prompts_in_interactive_terminal():
    options = SimpleNamespace(username="user", password=None)
    prompt = Mock(return_value="prompted-token")

    resolved = JenkinsInvoke.resolve_password(options, True, prompt)

    assert resolved.password == "prompted-token"
    prompt.assert_called_once_with("Jenkins password or API token: ")


def test_main_errors_for_non_interactive_missing_password(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["jenkins_invoke", "--username", "user", "job-one"]
    )

    class NonInteractiveStdin(object):
        @staticmethod
        def isatty():
            return False

    monkeypatch.setattr(sys, "stdin", NonInteractiveStdin())

    with pytest.raises(SystemExit) as exc:
        JenkinsInvoke.main()

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "Password/API token missing." in captured.err


def test_invokes_each_requested_job(monkeypatch):
    options = SimpleNamespace(
        baseurl="http://localhost:8080",
        username="user",
        password="token",
        block=True,
        token="job-token",
    )

    job = Mock()
    api = Mock()
    api.get_job.return_value = job
    monkeypatch.setattr(JenkinsInvoke, "_get_api", Mock(return_value=api))

    invoker = JenkinsInvoke(options, ["job-one", "job-two"])
    invoker()

    assert api.get_job.call_args_list == [call("job-one"), call("job-two")]
    assert job.invoke.call_args_list == [
        call(securitytoken="job-token", block=True),
        call(securitytoken="job-token", block=True),
    ]
