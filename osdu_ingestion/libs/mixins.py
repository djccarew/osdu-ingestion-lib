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

"""Mixins."""

from osdu_ingestion.libs.context import Context


class HeadersMixin:
    """Mixin for creating request headers to OSDU services using context."""

    def __init__(self, context: Context, *args, **kwargs):
        """Headers Mixin.

        :param context: Context dataclass that contains tenant information
        :type context: Context
        """
        self.context = context
        super().__init__(*args, **kwargs)

    @property
    def request_headers(self) -> dict:
        """Default request headers.

        :return: headers dict populated from Context
        :rtype: dict
        """
        headers = {
            'Content-type': 'application/json',
            'data-partition-id': self.context.data_partition_id,
            'AppKey': self.context.app_key
        }
        return headers
