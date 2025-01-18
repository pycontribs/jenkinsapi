"""
Module for jenkinsapi requester (which is a wrapper around python-requests)
"""

import requests
import urllib.parse as urlparse

from jenkinsapi.custom_exceptions import JenkinsAPIException, PostRequired

# import logging

# these two lines enable debugging at httplib level
# (requests->urllib3->httplib)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE
# with HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.
# import httplib
# httplib.HTTPConnection.debuglevel = 1

# you need to initialize logging, otherwise you will not see anything
# from requests
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

requests.adapters.DEFAULT_RETRIES = 5


class Requester(object):
    """
    A class which carries out HTTP requests. You can replace this
    class with one of your own implementation if you require some other
    way to access Jenkins.

    This default class can handle simple authentication only.
    """

    VALID_STATUS_CODES = [
        200,
    ]
    AUTH_COOKIE = None

    def __init__(self, *args, **kwargs):
        username = None
        password = None
        ssl_verify = True
        cert = None
        baseurl = None
        timeout = 10

        if len(args) == 1:
            (username,) = args
        elif len(args) == 2:
            username, password = args
        elif len(args) == 3:
            username, password, ssl_verify = args
        elif len(args) == 4:
            username, password, ssl_verify, cert = args
        elif len(args) == 5:
            username, password, ssl_verify, cert, baseurl = args
        elif len(args) == 6:
            username, password, ssl_verify, cert, baseurl, timeout = args
        elif len(args) > 6:
            raise ValueError("To much positional arguments given!")

        baseurl = kwargs.get("baseurl", baseurl)
        self.base_scheme = (
            urlparse.urlsplit(baseurl).scheme if baseurl else None
        )
        self.username = kwargs.get("username", username)
        self.password = kwargs.get("password", password)
        if self.username:
            assert self.password, (
                "Please provide both username and password "
                "or don't provide them at all"
            )
        if self.password:
            assert self.username, (
                "Please provide both username and password "
                "or don't provide them at all"
            )
        self.ssl_verify = kwargs.get("ssl_verify", ssl_verify)
        self.cert = kwargs.get("cert", cert)
        self.timeout = kwargs.get("timeout", timeout)
        self.session = requests.Session()
        self.max_retries = kwargs.get("max_retries")
        if self.max_retries is not None:
            retry_adapter = requests.adapters.HTTPAdapter(
                max_retries=self.max_retries
            )
            self.session.mount("http://", retry_adapter)
            self.session.mount("https://", retry_adapter)

    def get_request_dict(
        self, params=None, data=None, files=None, headers=None, **kwargs
    ):
        requestKwargs = kwargs
        if self.username:
            requestKwargs["auth"] = (self.username, self.password)

        if params:
            assert isinstance(
                params, dict
            ), "Params must be a dict, got %s" % repr(params)
            requestKwargs["params"] = params

        if headers:
            assert isinstance(
                headers, dict
            ), "headers must be a dict, got %s" % repr(headers)
            requestKwargs["headers"] = headers

        if self.AUTH_COOKIE:
            currentheaders = requestKwargs.get("headers", {})
            currentheaders.update({"Cookie": self.AUTH_COOKIE})
            requestKwargs["headers"] = currentheaders

        requestKwargs["verify"] = self.ssl_verify
        requestKwargs["cert"] = self.cert

        if data:
            # It may seem odd, but some Jenkins operations require posting
            # an empty string.
            requestKwargs["data"] = data

        if files:
            requestKwargs["files"] = files

        requestKwargs["timeout"] = self.timeout

        return requestKwargs

    def _update_url_scheme(self, url):
        """
        Updates scheme of given url to the one used in Jenkins baseurl.
        """
        if self.base_scheme and not url.startswith("%s://" % self.base_scheme):
            url_split = urlparse.urlsplit(url)
            url = urlparse.urlunsplit(
                [
                    self.base_scheme,
                    url_split.netloc,
                    url_split.path,
                    url_split.query,
                    url_split.fragment,
                ]
            )
        return url

    def get_url(
        self,
        url,
        params=None,
        headers=None,
        allow_redirects=True,
        stream=False,
    ):
        requestKwargs = self.get_request_dict(
            params=params,
            headers=headers,
            allow_redirects=allow_redirects,
            stream=stream,
        )
        return self.session.get(self._update_url_scheme(url), **requestKwargs)

    def post_url(
        self,
        url,
        params=None,
        data=None,
        files=None,
        headers=None,
        allow_redirects=True,
        **kwargs,
    ):
        requestKwargs = self.get_request_dict(
            params=params,
            data=data,
            files=files,
            headers=headers,
            allow_redirects=allow_redirects,
            **kwargs,
        )
        return self.session.post(self._update_url_scheme(url), **requestKwargs)

    def post_xml_and_confirm_status(
        self, url, params=None, data=None, valid=None
    ):
        headers = {"Content-Type": "text/xml"}
        return self.post_and_confirm_status(
            url, params=params, data=data, headers=headers, valid=valid
        )

    def post_and_confirm_status(
        self,
        url,
        params=None,
        data=None,
        files=None,
        headers=None,
        valid=None,
        allow_redirects=True,
    ):
        valid = valid or self.VALID_STATUS_CODES
        if not headers and not files:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

        assert data is not None, "Post messages must have data"

        response = self.post_url(
            url, params, data, files, headers, allow_redirects
        )
        if response.status_code not in valid:
            raise JenkinsAPIException(
                "Operation failed. url={0}, data={1}, headers={2}, "
                "status={3}, text={4}".format(
                    response.url,
                    data,
                    headers,
                    response.status_code,
                    response.text.encode("UTF-8"),
                )
            )
        return response

    def get_and_confirm_status(
        self, url, params=None, headers=None, valid=None, stream=False
    ):
        valid = valid or self.VALID_STATUS_CODES
        response = self.get_url(url, params, headers, stream=stream)
        if response.status_code not in valid:
            if response.status_code == 405:  # POST required
                raise PostRequired("POST required for url {0}".format(url))

            raise JenkinsAPIException(
                "Operation failed. url={0}, headers={1}, status={2}, "
                "text={3}".format(
                    response.url,
                    headers,
                    response.status_code,
                    response.text.encode("UTF-8"),
                )
            )
        return response
