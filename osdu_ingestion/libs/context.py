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

"""Context module."""

import dataclasses


@dataclasses.dataclass
class Context:
    """Class to store data-partition-id and AppKey."""

    data_partition_id: str
    app_key: str

    @classmethod
    def populate(cls, ctx: dict) -> 'Context':
        """
        Populates Context dataclass from dagrun.conf dict.

        :return: populated Context
        :rtype: Context
        """
        ctx_payload = ctx.pop('Payload')

        try:
            data_partition_id = ctx_payload['data-partition-id']
        except KeyError:
            data_partition_id = ctx['dataPartitionId'] # to support some DAGs payload interface

        ctx_obj = cls(app_key=ctx_payload['AppKey'],
                      data_partition_id=data_partition_id)

        return ctx_obj

