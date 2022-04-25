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


import os
import sys
import json
import http
import requests
import pytest



from mock_providers import get_test_credentials
from file_paths import (
    MANIFEST_WELLBORE_VALID_PATH
)
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.update_status import UpdateStatus
from mock_responses import MockWorkflowResponse


class TestUpdateStatus:

    @pytest.fixture()
    def status_updater(self, status: str, conf_path: str):
        with open(conf_path) as f:
            conf = json.load(f)
        context = Context.populate(conf["execution_context"])
        workflow_name = conf["workflow_name"]
        run_id = conf["run_id"]
        status_updater = UpdateStatus(
            workflow_name=workflow_name,
            workflow_url="http://test",
            workflow_id="",
            run_id=run_id,
            token_refresher=BaseTokenRefresher(get_test_credentials()),
            context=context,
            status=status
        )
        return status_updater

    @pytest.mark.parametrize(
        "conf_path,status",
        [
            pytest.param(
                MANIFEST_WELLBORE_VALID_PATH,
                http.HTTPStatus.OK
            )
        ]
    )
    def test_update_workflow_status(self, monkeypatch, status_updater: UpdateStatus, conf_path: str,
                                    status: str):
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockWorkflowResponse())
        monkeypatch.setattr(requests, "put", lambda *args, **kwargs: MockWorkflowResponse())
        status_updater.update_workflow_status()
