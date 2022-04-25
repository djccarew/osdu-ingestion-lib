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


ACL_DICT = {'viewers': ['data.default.viewers@odes.osdu.test.net'],'owners': ['data.default.owners@odes.osdu.test.net']}
LEGAL_DICT = {'legaltags': ['odes-demo-legaltag'], 'otherRelevantDataCountries': ['FR', 'US', 'CA'],'status': 'compliant'}

CONF = {
    "WorkProduct": {
        "ResourceTypeID": "srn:type:work-product/WellLog:",
        "ResourceSecurityClassification": "srn:reference-data/ResourceSecurityClassification:RESTRICTED:",
        "Data": {
            "GroupTypeProperties": {
                "Components": []
            },
            "IndividualTypeProperties": {
                "Name": "Test AKM LOG 111",
                "Description": "Well Log"
            },
            "ExtensionProperties": {}
        },
        "ComponentsAssociativeIDs": [
            "wpc-1"
        ]
    },
    "WorkProductComponents": [
        {
            "ResourceTypeID": "srn:type:work-product-component/WellLog:",
            "ResourceSecurityClassification": "srn:reference-data/ResourceSecurityClassification:RESTRICTED:",
            "Data": {
                "GroupTypeProperties": {
                    "Files": [],
                    "Artefacts": []
                },
                "AssociativeID": "wpc-1",
                "FileAssociativeIDs": [
                    "f-1"
                ]
            }
        }
    ],
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "test",
        "AppKey": "test",
        "kind_version": "3.0.0",
        "acl": {
            "viewers": ["data.default.viewers@odes.osdu.joonix.net"],
            "owners": ["data.default.owners@odes.osdu.joonix.net"]},
        "legal": {
            "legaltags": ["odes-demo-legaltag"],
            "otherRelevantDataCountries": ["FR", "US", "CA"]}
    },
    "Files": [
        {
            "ResourceTypeID": "srn:type:file/las2:",
            "ResourceSecurityClassification": "srn:reference-data/ResourceSecurityClassification:RESTRICTED:",
            "Data": {
                "GroupTypeProperties": {
                    "FileSource": "",
                    "PreLoadFilePath": "foo"
                },
                "IndividualTypeProperties": {},
                "ExtensionProperties": {}
            },
            "AssociativeID": "f-1"
        }
    ],
    "WorkflowID": "foo"
}

PROCESS_FILE_ITEMS_RESULT = (
    [
        (
            {
                'kind': 'test:osdu:file:3.0.0',
                'legal': {'legaltags': ['odes-demo-legaltag'], 'otherRelevantDataCountries': ['US'], 'status': 'compliant'},
                'acl': {'viewers': ['data.default.viewers@odes.osdu.test.net'],
                        'owners': ['data.default.owners@odes.osdu.test.net']},
                'data': {
                    'ResourceTypeID': 'srn:type:file/las2:',
                    'ResourceSecurityClassification': 'srn:reference-data/ResourceSecurityClassification:RESTRICTED:',
                    'Data': {'GroupTypeProperties': {'FileSource': '', 'PreLoadFilePath': 'foo'}, 'IndividualTypeProperties': {}, 'ExtensionProperties': {}},
                    'AssociativeID': 'f-1',
                    'ResourceID': ""
                }
            },
            'File'
        )
    ],
    ['srn:file/las2:434064998475386:']
)

LOADED_CONF = {
        "acl": ACL_DICT,
        "legal_tag": LEGAL_DICT,
        "data_object": CONF
    }

CONF_PAYLOAD = CONF["Payload"]


class DAG_RUN:
    def __init__(self):
        self.conf = CONF


DAG_RUN_CONF = {
    "dag_run": DAG_RUN()
}
