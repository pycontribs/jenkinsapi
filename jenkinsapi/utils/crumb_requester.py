# Code from https://github.com/ros-infrastructure/ros_buildfarm
# (c) Open Source Robotics Foundation
import ast
import logging
from jenkinsapi.utils.requester import Requester

logger = logging.getLogger(__name__)


class CrumbRequester(Requester):
    """Adapter for Requester inserting the crumb in every request."""

    def __init__(self, *args, **kwargs):
        super(CrumbRequester, self).__init__(*args, **kwargs)
        self._baseurl = kwargs["baseurl"]
        self._last_crumb_data = None

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
        if self._last_crumb_data:
            # first try request with previous crumb if available
            response = self._post_url_with_crumb(
                self._last_crumb_data,
                url,
                params,
                data,
                files,
                headers,
                allow_redirects,
                **kwargs,
            )
            # code 403 might indicate that the crumb is not valid anymore
            if response.status_code != 403:
                return response

        # fetch new crumb (if server has crumbs enabled)
        if self._last_crumb_data is not False:
            self._last_crumb_data = self._get_crumb_data()

        return self._post_url_with_crumb(
            self._last_crumb_data,
            url,
            params,
            data,
            files,
            headers,
            allow_redirects,
            **kwargs,
        )

    def _get_crumb_data(self):
        response = self.get_url(self._baseurl + "/crumbIssuer/api/python")
        if response.status_code in [404]:
            logger.warning("The Jenkins master does not require a crumb")
            return False
        if response.status_code not in [200]:
            raise RuntimeError("Failed to fetch crumb: %s" % response.text)
        crumb_issuer_response = ast.literal_eval(response.text)
        crumb_request_field = crumb_issuer_response["crumbRequestField"]
        crumb = crumb_issuer_response["crumb"]
        logger.debug("Fetched crumb: %s", crumb)
        return {crumb_request_field: crumb}

    def _post_url_with_crumb(
        self,
        crumb_data,
        url,
        params,
        data,
        files,
        headers,
        allow_redirects,
        **kwargs,
    ):
        if crumb_data:
            if headers is None:
                headers = crumb_data
            else:
                headers.update(crumb_data)

        return super(CrumbRequester, self).post_url(
            url, params, data, files, headers, allow_redirects, **kwargs
        )
