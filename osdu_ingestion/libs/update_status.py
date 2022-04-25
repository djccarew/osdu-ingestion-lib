#  Copyright 2020 Google LLC
#  Copyright 2020 EPAM Systems
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Provides UpdateStatus processor."""

import json
import logging

import requests
from osdu_api.auth.authorization import TokenRefresher, authorize

from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.mixins import HeadersMixin

logger = logging.getLogger()


class UpdateStatus(HeadersMixin):
    """Class to perform update status of the workflow."""

    def __init__(
        self,
        workflow_name: str,
        workflow_id: str,
        run_id: str,
        workflow_url: str,
        status: str,
        token_refresher: TokenRefresher,
        context: Context,
    ) -> None:
        """Init the status update processor.

        :param workflow_name: the name of the workflow
        :type workflow_name: str
        :param workflow_id: The id of the workflow
        :type workflow_id: str
        :param run_id: The id of workflow run instance
        :type run_id: str
        :param workflow_url: The base url of the Workflow service
        :type workflow_url: str
        :param status: The status
        :type status: str
        :param token_refresher: An instance of token refresher
        :type token_refresher: TokenRefresher
        :param context: The tenant context
        :type context: Context
        """
        super().__init__(context)
        self.workflow_name = workflow_name
        self.workflow_url = workflow_url
        self.workflow_id = workflow_id
        self.run_id = run_id
        self.context = context
        self.status = status
        self.token_refresher = token_refresher

    @authorize()
    def update_status_request(self, headers: dict) -> requests.Response:
        """Send request to update status.

        :param headers: The request headers
        :type headers: dict
        :return: The Workflow server response
        :rtype: requests.Response
        """
        request_body = {
            "status": self.status
        }
        request_body = json.dumps(request_body)
        logger.debug(f"Sending request '{request_body}'")
        update_status_url = f"{self.workflow_url}/v1/workflow/{self.workflow_name}/workflowRun/{self.run_id}"
        logger.debug(f"Workflow URL: {update_status_url}")
        response = requests.put(update_status_url, request_body, headers=headers)
        return response

    @authorize()
    def update_status_request_old(self, headers: dict) -> requests.Response:
        """Send request to update status.

        :param headers: The request headers
        :type headers: dict
        :return: The Workflow server response
        :rtype: requests.Response
        """
        request_body = {
            "WorkflowID": self.workflow_id,
            "Status": self.status
        }
        request_body = json.dumps(request_body)
        logger.debug(f" Sending request '{request_body}'")
        response = requests.post(self.workflow_url, request_body, headers=headers)
        return response

    def update_workflow_status(self):
        """Updates workflow status."""
        headers = self.request_headers
        if self.workflow_name:
            self.update_status_request(headers)
        else:
            self.update_status_request_old(headers)
