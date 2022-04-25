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


ACL_DICT = {'viewers': ['data.default.viewers@odes.osdu.test.net'],
            'owners': ['data.default.owners@odes.osdu.test.net']}
LEGAL_DICT = {'legaltags': ['odes-demo-legaltag'], 'otherRelevantDataCountries': ['FR', 'US', 'CA'],
              'status': 'compliant'}

CONF_LOAD_WELL_13104 = {
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "opendes",
        "AppKey": "",
        "kind_version": "3.0.0"
    },
    "$schema": "https://schema.osdu.opengroup.org/json/master-data/Wellbore.1.0.0.json",
    "$filename": "load_Wellbore.1.0.0_350112350400.json",
    "manifest": [
        {

            "id": "srn:opendes:master-data/Well:131041",
            "version": 1,
            "kind": "opendes:osdu:Well:0.3.0",
            "groupType": "master-data",
            "acl": {
                "owners": [
                    "ownergroup@testcompany.com"
                ],
                "viewers": [
                    "viewgroup@testcompany.com"
                ]
            },
            "legal": {
                "legaltags": [
                    "legaltag"
                ],
                "otherRelevantDataCountries": [
                    "GB"
                ]
            },
            "resourceObjectCreationDateTime": "2012-03-19T07:22Z",
            "resourceVersionCreationDateTime": "2012-03-19T07:22Z",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:Public:1",
            "data": {
                "FacilityTypeID": "srn:opendes:reference-data/FacilityType:WELL:1",
                "FacilityOperator": [
                    {
                        "FacilityOperatorOrganisationID": "srn:opendes:master-data/Organisation:CHRYSAOR PRODUCTION (U.K.) LIMITED:1"
                    }
                ],
                "DataSourceOrganisationID": "srn:opendes:master-data/Organisation:UK_OGA:1",
                "SpatialLocation": [
                    {
                        "Wgs84Coordinates": {
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [
                                            1.896235806,
                                            53.72433018
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ],
                "FacilityName": "48/10b-N2",
                "FacilityNameAlias": [
                    {
                        "AliasName": "48/10b-N2",
                        "AliasNameTypeID": "srn:opendes:reference-data/AliasNameType:WELL_NAME:1"
                    }
                ],
                "FacilityState": [
                    {
                        "FacilityStateTypeID": "srn:opendes:reference-data/FacilityStateType:PLUGGED:1"
                    }
                ],
                "FacilityEvent": [
                    {
                        "FacilityEventTypeID": "srn:opendes:reference-data/FacilityEventType:SPUD_DATE:1",
                        "EffectiveDateTime": "2005-08-14T00:00:00"
                    }
                ],
                "VerticalMeasurements": [
                    {
                        "VerticalMeasurementID": "RT",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:DEPTH_DATUM_ELEV:1",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:M:1"
                    }
                ]
            }

        }
    ]
}


CONF_CONTRACTOR_TYPE = {
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "opendes",
        "AppKey": "",
    },
    "$schema": "https://schema.osdu.opengroup.org/json/master-data/Wellbore.1.0.0.json",
    "manifest": [
        {
            "id": "srn:opendes:reference-data/ContractorType:1",
            "kind": "opendes:osdu:ContractorType:1.0.0",
            "groupType": "reference-data",
            "version": 1,
            "acl": {"viewers": ["data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"],
                    "owners": ["data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"]},
            "legal": {"legaltags": ["opendes-demo-legaltag"], "otherRelevantDataCountries": ["US"],
                      "status": "compliant"},
            "resourceHomeRegionID": "srn:opendes:reference-data/OSDURegion:US-EAST:1",
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:1"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceCurationStatus": "srn:opendes:reference-data/ResourceCurationStatus:CURATED:1",
            "resourceLifecycleStatus": "srn:opendes:reference-data/ResourceLifecycleStatus:LOADING:1",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:1",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:1",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:1",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:1",
            "data": {
                "Name": "Recording",
                "Description": "Performs data acquistion",
                "Code": "Record"
            }
        },
        {
            "id": "srn:opendes:reference-data/ContractorType:1",
            "kind": "opendes:osdu:ContractorType:1.0.0",
            "groupType": "reference-data",
            "version": 1,
            "acl": {"viewers": ["data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"],
                    "owners": ["data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"]},
            "legal": {"legaltags": ["opendes-demo-legaltag"], "otherRelevantDataCountries": ["US"],
                      "status": "compliant"},
            "resourceHomeRegionID": "srn:opendes:reference-data/OSDURegion:US-EAST:1",
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:1"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceCurationStatus": "srn:opendes:reference-data/ResourceCurationStatus:CURATED:1",
            "resourceLifecycleStatus": "srn:opendes:reference-data/ResourceLifecycleStatus:LOADING:1",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:1",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:1",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:1",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:1",
            "data": {
                "Name": "Line Clearing",
                "Description": "Prepares onshore swath access",
                "Code": "LineClear"
            }
        },
        {
            "id": "srn:opendes:reference-data/ContractorType:1",
            "kind": "opendes:osdu:ContractorType:1.0.0",
            "groupType": "reference-data",
            "version": 1,
            "acl": {"viewers": ["data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"],
                    "owners": ["data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"]},
            "legal": {"legaltags": ["opendes-demo-legaltag"], "otherRelevantDataCountries": ["US"],
                      "status": "compliant"},
            "resourceHomeRegionID": "srn:opendes:reference-data/OSDURegion:US-EAST:1",
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:1"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceCurationStatus": "srn:opendes:reference-data/ResourceCurationStatus:CURATED:1",
            "resourceLifecycleStatus": "srn:opendes:reference-data/ResourceLifecycleStatus:LOADING:1",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:1",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:1",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:1",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:1",
            "data": {
                "Name": "Positioning",
                "Description": "Establishes location of surface equipment",
                "Code": "Position"
            }
        },
        {
            "id": "srn:opendes:reference-data/ContractorType:1",
            "kind": "opendes:osdu:ContractorType:1.0.0",
            "groupType": "reference-data",
            "version": 1,
            "acl": {"viewers": ["data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"],
                    "owners": ["data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"]},
            "legal": {"legaltags": ["opendes-demo-legaltag"], "otherRelevantDataCountries": ["US"],
                      "status": "compliant"},
            "resourceHomeRegionID": "srn:opendes:reference-data/OSDURegion:US-EAST:1",
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:1"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceCurationStatus": "srn:opendes:reference-data/ResourceCurationStatus:CURATED:",
            "resourceLifecycleStatus": "srn:opendes:reference-data/ResourceLifecycleStatus:LOADING:",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:",
            "data": {
                "Name": "Data Processing",
                "Description": "Transforms data",
                "Code": "DataProc"
            }
        }
    ]
}


CONF = {
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "opendes",
        "AppKey": "",
        "kind_version": "3.0.0"
    },
    "$schema": "https://schema.osdu.opengroup.org/json/master-data/Wellbore.1.0.0.json",
    "$filename": "load_Wellbore.1.0.0_350112350400.json",
    "manifest": [
        {
            "id": "srn:opendes:master-data/Wellbore:350112350400",
            "kind": "opendes:osdu:Wellbore:0.3.0",
            "groupType": "master-data",
            "version": 1,
            "acl": {
                "owners": [
                    "data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ],
                "viewers": [
                    "data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ]
            },
            "legal": {
                "legaltags": [
                    "opendes-demo-legaltag"
                ],
                "otherRelevantDataCountries": [
                    "srn:opendes:master-data/GeoPoliticalEntity:USA:"
                ],
                "status": "srn:opendes:reference-data/LegalStatus:public:1111"
            },
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:",
            "data": {
                "FacilityTypeID": "srn:opendes:reference-data/FacilityType:Wellbore:",
                "FacilityOperator": [
                    {
                        "FacilityOperatorOrganisationID": "srn:opendes:master-data/Organisation:CONTINENTAL RESOURCES INC:"
                    }
                ],
                "DataSourceOrganisationID": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:",
                "SpatialLocation": [
                    {
                        "Coordinates": [
                            {
                                "x": -98.580887,
                                "y": 35.6381829999999
                            }
                        ],
                        "SpatialGeometryTypeID": "srn:opendes:reference-data/SpatialGeometryType:Point:",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:",
                        "HorizontalCRSID": "srn:opendes:reference-data/HorizontalCRS:NAD27:",
                        "HeightAboveGroundLevelUOMID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:"
                    }
                ],
                "OperatingEnvironmentID": "srn:opendes:reference-data/OperatingEnvironment:onshore:",
                "FacilityName": "IRETA 1-4-9XH",
                "FacilityNameAlias": [
                    {
                        "AliasName": " IRETA 1-4-9XH",
                        "AliasNameTypeID": "srn:opendes:reference-data/AliasNameType:Name:"
                    },
                    {
                        "AliasName": "350112350400",
                        "AliasNameTypeID": "srn:opendes:reference-data/AliasNameType:UWBI:"
                    }
                ],
                "FacilityEvent": [
                    {
                        "FacilityEventTypeID": "srn:opendes:reference-data/FacilityEventType:SPUD:",
                        "EffectiveDateTime": "2015-03-11T00:00:00-05:00"
                    },
                    {
                        "FacilityEventTypeID": "srn:opendes:reference-data/FacilityEventType:DRILLING FINISH:",
                        "EffectiveDateTime": "2015-05-18T00:00:00-06:00"
                    }
                ],
                "WellID": "srn:opendes:master-data/Well:3501123504:",
                "SequenceNumber": 1,
                "VerticalMeasurements": [
                    {
                        "VerticalMeasurementID": "TD_1",
                        "VerticalMeasurement": 0,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Total Depth:",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Measured Depth:",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:",
                        "VerticalReferenceID": "Drill Floor"
                    },
                    {
                        "VerticalMeasurementID": "TD_2",
                        "VerticalMeasurement": 0,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Total Depth:",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:True Vertical Depth:",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:",
                        "VerticalReferenceID": "Drill Floor"
                    },
                    {
                        "VerticalMeasurementID": "Elev_1",
                        "VerticalMeasurement": 1636,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Drill Floor:",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Elevation:",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:"
                    },
                    {
                        "VerticalMeasurementID": "Elev_2",
                        "VerticalMeasurement": 1606,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Ground Level:",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Elevation:",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:"
                    }
                ],
                "TrajectoryTypeID": "srn:opendes:reference-data/WellboreTrajectoryType:Horizontal:",
                "DefaultVerticalMeasurementID": "",
                "GeographicBottomHoleLocation": {
                    "Coordinates": [
                        {
                            "x": -98.580887,
                            "y": 35.6381829999999
                        }
                    ]
                }
            }
        }

    ],
    "WorkflowID": "foo"
}

CONF_TEST_REFERENCE = {
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "opendes",
        "AppKey": "",
        "kind_version": "3.0.0"
    },
    "$schema": "https://schema.osdu.opengroup.org/json/master-data/Wellbore.1.0.0.json",
    "$filename": "load_Wellbore.1.0.0_350112350400.json",
    "manifest": [

        {
            "kind": "opendes:osdu:TestReference:1.0.1",
            "groupType": "reference-data",
            "acl": {
                "owners": [
                    "data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ],
                "viewers": [
                    "data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ]
            },
            "legal": {
                "legaltags": [
                    "opendes-demo-legaltag"
                ],
                "otherRelevantDataCountries": [
                    "US"
                ],
                "status": "compliant"
            },
            "data": {
                "Name": "TestReference",
                "Description": "A meaningful description of this TestReference.",
                "Schema": "http://json-schema.org/draft-07/schema#",
                "SchemaID": "https://schema.osdu.opengroup.org/json/reference-data/TestReference.1.0.0.json",
                "SchemaKind": "osdu:osdu:TestReference:1.0.0",
                "GroupType": "reference-data",
                "IsReferenceValueType": True,
                "GovernanceAuthorities": [
                    "$$srn:NAMESPACE$$:reference-data/OrganisationType:osdu"
                ],
                "NaturalKeys": [
                    "data.Code",
                    "data.Name"
                ],
                "GovernanceModel": "LOCAL"
            }
        }

    ],
    "WorkflowID": "foo"
}


CONF2 = {
    "WorkflowID": "{{workflow_id}}",
    "Payload": {
        "AppKey": "",
        "data-partition-id": "opendes"
    },
    "manifest": [
        {
            "id": "srn:opendes:master-data/Wellbore:350112350400",
            "kind": "osdu:osdu:Wellbore:0.3.0",
            "groupType": "master-data",
            "version": 1,
            "acl": {
                "Viewers": [
                    "data.default.viewers@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ],
                "Owners": [
                    "data.default.owners@opendes.osdu-gcp.go3-nrg.projects.epam.com"
                ]
            },
            "legal": {
                "LegalTags": [
                    "legaltag1"
                ],
                "OtherRelevantDataCountries": [
                    "srn:opendes:master-data/GeoPoliticalEntity:USA:"
                ],
                "Status": "srn:opendes:reference-data/LegalStatus:public:"
            },
            "resourceHostRegionIDs": [
                "srn:opendes:reference-data/OSDURegion:US-EAST:"
            ],
            "resourceObjectCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceVersionCreationDateTime": "2020-10-16T11:14:45-05:00",
            "resourceSecurityClassification": "srn:opendes:reference-data/ResourceSecurityClassification:public:",
            "source": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:",
            "existenceKind": "srn:opendes:reference-data/ExistenceKind:Active:",
            "licenseState": "srn:opendes:reference-data/LicenseState:Unlicensed:",
            "data": {
                "FacilityTypeID": "srn:opendes:reference-data/FacilityType:Wellbore:",
                "FacilityOperator": [
                    {
                        "FacilityOperatorOrganisationID": "srn:opendes:master-data/Organisation:CONTINENTAL RESOURCES INC:"
                    }
                ],
                "DataSourceOrganisationID": "srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:",
                "SpatialLocation": [
                    {
                        "Coordinates": [
                            {
                                "x": -98.580887,
                                "y": 35.6381829999999
                            }
                        ],
                        "SpatialGeometryTypeID": "srn:opendes:reference-data/SpatialGeometryType:Point:1",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:1",
                        "HorizontalCRSID": "srn:opendes:reference-data/HorizontalCRS:NAD27:1",
                        "HeightAboveGroundLevelUOMID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:1"
                    }
                ],
                "OperatingEnvironmentID": "srn:opendes:reference-data/OperatingEnvironment:onshore:1",
                "FacilityName": "IRETA 1-4-9XH",
                "FacilityNameAlias": [
                    {
                        "AliasName": " IRETA 1-4-9XH",
                        "AliasNameTypeID": "srn:opendes:reference-data/AliasNameType:Name:1"
                    },
                    {
                        "AliasName": "350112350400",
                        "AliasNameTypeID": "srn:opendes:reference-data/AliasNameType:UWBI:1"
                    }
                ],
                "FacilityEvent": [
                    {
                        "FacilityEventTypeID": "srn:opendes:reference-data/FacilityEventType:SPUD:1",
                        "EffectiveDateTime": "2015-03-11T00:00:00-05:00"
                    },
                    {
                        "FacilityEventTypeID": "srn:opendes:reference-data/FacilityEventType:DRILLING FINISH:1",
                        "EffectiveDateTime": "2015-05-18T00:00:00-06:00"
                    }
                ],
                "WellID": "srn:opendes:master-data/Well:3501123504:1",
                "SequenceNumber": 1,
                "VerticalMeasurements": [
                    {
                        "VerticalMeasurementID": "TD_1",
                        "VerticalMeasurement": 0,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Total Depth:1",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Measured Depth:1",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:1",
                        "VerticalReferenceID": "Drill Floor"
                    },
                    {
                        "VerticalMeasurementID": "TD_2",
                        "VerticalMeasurement": 0,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Total Depth:1",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:True Vertical Depth:1",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:1",
                        "VerticalReferenceID": "Drill Floor"
                    },
                    {
                        "VerticalMeasurementID": "Elev_1",
                        "VerticalMeasurement": 1636,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Drill Floor:1",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Elevation:1",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:1",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:1"
                    },
                    {
                        "VerticalMeasurementID": "Elev_2",
                        "VerticalMeasurement": 1606,
                        "VerticalMeasurementTypeID": "srn:opendes:reference-data/VerticalMeasurementType:Ground Level:1",
                        "VerticalMeasurementPathID": "srn:opendes:reference-data/VerticalMeasurementPath:Elevation:1",
                        "VerticalMeasurementUnitOfMeasureID": "srn:opendes:reference-data/UnitOfMeasure:ft[US]:1",
                        "VerticalCRSID": "srn:opendes:reference-data/VerticalCRS:MSL:1"
                    }
                ],
                "TrajectoryTypeID": "srn:opendes:reference-data/WellboreTrajectoryType:Horizontal:1",
                "DefaultVerticalMeasurementID": "",
                "GeographicBottomHoleLocation": {
                    "Coordinates": [
                        {
                            "x": -98.580887,
                            "y": 35.6381829999999
                        }
                    ]
                }
            }
        }
    ]
}

TEST_SCHEMA = {
    "x-osdu-license": "Copyright 2020, The Open Group \\nLicensed under the Apache License, Version 2.0 (the \"License\"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 . Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an \"AS IS\" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.",
    "$id": "https://schema.osdu.opengroup.org/json/reference-data/ContractorType.1.0.0.json",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Test",
    "description": "Test.",
    "type": "object",
    "properties": {
        "id": {
            "description": "The SRN which identifies this OSDU resource object without version.",
            "title": "Entity ID",
            "type": "string",
            "pattern": "^srn:opendes:master-data\\/Wellbore:[^:]+$",
            "example": "srn:opendes:master-data/Wellbore:2adac27b-5d84-5bcd-89f2-93ee709c06d9"
        },
        "kind": {
            "description": "The schema identification for the OSDU resource object following the pattern opendes:<Source>:<Type>:<VersionMajor>.<VersionMinor>.<VersionPatch>. The versioning scheme follows the semantic versioning, https://semver.org/.",
            "title": "Entity Kind",
            "type": "string",
            "pattern": "^[A-Za-z0-9-_]+:[A-Za-z0-9-_]+:[A-Za-z0-9-_]+:[0-9]+.[0-9]+.[0-9]+$",
            "example": "namespace:osdu:Wellbore:2.7.112"
        },
        "groupType": {
            "description": "The OSDU GroupType assigned to this resource object.",
            "title": "Group Type",
            "const": "master-data"
        },
        "version": {
            "description": "The version number of this OSDU resource; set by the framework.",
            "title": "Version Number",
            "type": "integer",
            "format": "int64",
            "example": 1831253916104085
        },
        "acl": {
            "description": "The access control tags associated with this entity.",
            "title": "Access Control List",
            "type": "object"
        },
        "legal": {
            "description": "The entity's legal tags and compliance status.",
            "title": "Legal Tags",
            "type": "object"
        },
        "resourceHomeRegionID": {
            "description": "The name of the home [cloud environment] region for this OSDU resource object.",
            "title": "Resource Home Region ID",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/OSDURegion:[^:]+:[0-9]*$"
        },
        "resourceHostRegionIDs": {
            "description": "The name of the host [cloud environment] region(s) for this OSDU resource object.",
            "title": "Resource Host Region ID",
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^srn:opendes:reference-data\\/OSDURegion:[^:]+:[0-9]*$"
            }
        },
        "resourceObjectCreationDateTime": {
            "description": "Timestamp of the time at which Version 1 of this OSDU resource object was originated.",
            "title": "Resource Object Creation DateTime",
            "type": "string",
            "format": "date-time"
        },
        "resourceVersionCreationDateTime": {
            "description": "Timestamp of the time when the current version of this resource entered the OSDU.",
            "title": "Resource Version Creation DateTime",
            "type": "string",
            "format": "date-time"
        },
        "resourceCurationStatus": {
            "description": "Describes the current Curation status.",
            "title": "Resource Curation Status",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/ResourceCurationStatus:[^:]+:[0-9]*$"
        },
        "resourceLifecycleStatus": {
            "description": "Describes the current Resource Lifecycle status.",
            "title": "Resource Lifecycle Status",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/ResourceLifecycleStatus:[^:]+:[0-9]*$"
        },
        "resourceSecurityClassification": {
            "description": "Classifies the security level of the resource.",
            "title": "Resource Security Classification",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/ResourceSecurityClassification:[^:]+:[0-9]*$"
        },
        "ancestry": {
            "description": "The links to data, which constitute the inputs.",
            "title": "Ancestry",
            "$ref": "osdu:osdu:AbstractLegalParentList:1.0.0"
        },
        "source": {
            "description": "Where did the data resource originate? This could be many kinds of entities, such as company, agency, team or individual.",
            "title": "Data Source",
            "type": "string",
            "pattern": "^srn:opendes:master-data\\/Organisation:[^:]+:[0-9]*$"
        },
        "existenceKind": {
            "description": "Where does this data resource sit in the cradle-to-grave span of its existence?",
            "title": "Existence Kind",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/ExistenceKind:[^:]+:[0-9]*$"
        },
        "licenseState": {
            "description": "Indicates what kind of ownership Company has over data.",
            "title": "License State",
            "type": "string",
            "pattern": "^srn:opendes:reference-data\\/LicenseState:[^:]+:[0-9]*$"
        },
        "data": {
            "allOf": [
                {
                    "type": "object",
                    "properties": {
                        "WellID": {
                            "type": "string"
                        }
                    }
                }
            ]
        },
        "required": [
            "kind",
            "acl",
            "groupType",
            "legal"
        ],
        "additionalProperties": False
    }
}

EMPTY_MANIFEST = {
    "Payload": {
        "authorization": "Bearer test",
        "data-partition-id": "osdu",
        "AppKey": "",
        "kind_version": "3.0.0"
    },
    "$schema": "https://schema.osdu.opengroup.org/json/master-data/Wellbore.1.0.0.json",
    "$filename": "load_Wellbore.1.0.0_350112350400.json",
    "manifest": [],
    "WorkflowID": "foo"
}

EXPECTED_RECORD = [{'legal': {'LegalTags': ['legaltag1'], 'OtherRelevantDataCountries': [
    'srn:opendes:master-data/GeoPoliticalEntity:USA:'],
                              'Status': 'srn:opendes:reference-data/LegalStatus:public:'},
                    'acl': {'Owners': ['users@odes.osdu.joonix.net'],
                            'Viewers': ['users@odes.osdu.joonix.net']},
                    'kind': 'osdu:osdu:Wellbore:0.3.0', 'id': '',
                    'data': {'id': 'srn:opendes:master-data/Wellbore:350112350400',
                             'groupType': 'master-data', 'version': 1, 'resourceHostRegionIDs': [
                            'srn:opendes:reference-data/OSDURegion:US-EAST:'],
                             'resourceObjectCreationDateTime': '2020-10-16T11:14:45-05:00',
                             'resourceVersionCreationDateTime': '2020-10-16T11:14:45-05:00',
                             'resourceSecurityClassification': 'srn:opendes:reference-data/ResourceSecurityClassification:public:',
                             'source': 'srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:',
                             'existenceKind': 'srn:opendes:reference-data/ExistenceKind:Active:',
                             'licenseState': 'srn:opendes:reference-data/LicenseState:Unlicensed:',
                             'data': {
                                 'FacilityTypeID': 'srn:opendes:reference-data/FacilityType:Wellbore:',
                                 'FacilityOperator': [{
                                     'FacilityOperatorOrganisationID': 'srn:opendes:master-data/Organisation:CONTINENTAL RESOURCES INC:'}],
                                 'DataSourceOrganisationID': 'srn:opendes:master-data/Organisation:Oklahoma Corporation Commission:',
                                 'SpatialLocation': [
                                     {'Coordinates': [{'x': -98.580887, 'y': 35.6381829999999}],
                                      'SpatialGeometryTypeID': 'srn:opendes:reference-data/SpatialGeometryType:Point:',
                                      'VerticalCRSID': 'srn:opendes:reference-data/VerticalCRS:MSL:',
                                      'HorizontalCRSID': 'srn:opendes:reference-data/HorizontalCRS:NAD27:',
                                      'HeightAboveGroundLevelUOMID': 'srn:opendes:reference-data/UnitOfMeasure:ft[US]:'}],
                                 'OperatingEnvironmentID': 'srn:opendes:reference-data/OperatingEnvironment:onshore:',
                                 'FacilityName': 'IRETA 1-4-9XH', 'FacilityNameAlias': [
                                     {'AliasName': ' IRETA 1-4-9XH',
                                      'AliasNameTypeID': 'srn:opendes:reference-data/AliasNameType:Name:'},
                                     {'AliasName': '350112350400',
                                      'AliasNameTypeID': 'srn:opendes:reference-data/AliasNameType:UWBI:'}],
                                 'FacilityEvent': [{
                                     'FacilityEventTypeID': 'srn:opendes:reference-data/FacilityEventType:SPUD:',
                                     'EffectiveDateTime': '2015-03-11T00:00:00-05:00'},
                                     {
                                         'FacilityEventTypeID': 'srn:opendes:reference-data/FacilityEventType:DRILLING FINISH:',
                                         'EffectiveDateTime': '2015-05-18T00:00:00-06:00'}],
                                 'WellID': 'srn:opendes:master-data/Well:3501123504:',
                                 'SequenceNumber': 1, 'VerticalMeasurements': [
                                     {'VerticalMeasurementID': 'TD_1', 'VerticalMeasurement': 0,
                                      'VerticalMeasurementTypeID': 'srn:opendes:reference-data/VerticalMeasurementType:Total Depth:',
                                      'VerticalMeasurementPathID': 'srn:opendes:reference-data/VerticalMeasurementPath:Measured Depth:',
                                      'VerticalMeasurementUnitOfMeasureID': 'srn:opendes:reference-data/UnitOfMeasure:ft[US]:',
                                      'VerticalReferenceID': 'Drill Floor'},
                                     {'VerticalMeasurementID': 'TD_2', 'VerticalMeasurement': 0,
                                      'VerticalMeasurementTypeID': 'srn:opendes:reference-data/VerticalMeasurementType:Total Depth:',
                                      'VerticalMeasurementPathID': 'srn:opendes:reference-data/VerticalMeasurementPath:True Vertical Depth:',
                                      'VerticalMeasurementUnitOfMeasureID': 'srn:opendes:reference-data/UnitOfMeasure:ft[US]:',
                                      'VerticalReferenceID': 'Drill Floor'},
                                     {'VerticalMeasurementID': 'Elev_1',
                                      'VerticalMeasurement': 1636,
                                      'VerticalMeasurementTypeID': 'srn:opendes:reference-data/VerticalMeasurementType:Drill Floor:',
                                      'VerticalMeasurementPathID': 'srn:opendes:reference-data/VerticalMeasurementPath:Elevation:',
                                      'VerticalMeasurementUnitOfMeasureID': 'srn:opendes:reference-data/UnitOfMeasure:ft[US]:',
                                      'VerticalCRSID': 'srn:opendes:reference-data/VerticalCRS:MSL:'},
                                     {'VerticalMeasurementID': 'Elev_2',
                                      'VerticalMeasurement': 1606,
                                      'VerticalMeasurementTypeID': 'srn:opendes:reference-data/VerticalMeasurementType:Ground Level:',
                                      'VerticalMeasurementPathID': 'srn:opendes:reference-data/VerticalMeasurementPath:Elevation:',
                                      'VerticalMeasurementUnitOfMeasureID': 'srn:opendes:reference-data/UnitOfMeasure:ft[US]:',
                                      'VerticalCRSID': 'srn:opendes:reference-data/VerticalCRS:MSL:'}],
                                 'TrajectoryTypeID': 'srn:opendes:reference-data/WellboreTrajectoryType:Horizontal:',
                                 'DefaultVerticalMeasurementID': '',
                                 'GeographicBottomHoleLocation': {
                                     'Coordinates': [{'x': -98.580887, 'y': 35.6381829999999}]}}}},
                   {'legal': {'legaltags': ['$$LEGAL_TAG$$'],
                              'otherRelevantDataCountries': ['$$ISO_3166_ALPHA_2_CODE$$']},
                    'acl': {'owners': ['$$DATA_OWNERS_GROUP$$'],
                            'viewers': ['$$DATA_VIEWERS_GROUP$$']},
                    'kind': 'osdu:osdu:TestReference:1.0.0', 'id': '',
                    'data': {'id': '$$srn:NAMESPACE$$:type/Type:TestReference', 'groupType': 'type',
                             'data': {'Name': 'TestReference',
                                      'Description': 'A meaningful description of this TestReference.',
                                      'Schema': 'http://json-schema.org/draft-07/schema#',
                                      'SchemaID': 'https://schema.osdu.opengroup.org/json/reference-data/TestReference.1.0.0.json',
                                      'SchemaKind': 'osdu:osdu:TestReference:1.0.0',
                                      'GroupType': 'reference-data', 'IsReferenceValueType': True,
                                      'GovernanceAuthorities': [
                                          '$$srn:NAMESPACE$$:reference-data/OrganisationType:osdu'],
                                      'NaturalKeys': ['data.Code', 'data.Name'],
                                      'GovernanceModel': 'LOCAL'}}}, {
                       'legal': {'legalTags': ['$$LEGAL_TAG$$'],
                                 'otherRelevantDataCountries': ['$$ISO_3166_ALPHA_2_CODE$$']},
                       'acl': {'owners': ['$$DATA_OWNERS_GROUP$$'],
                               'viewers': ['$$DATA_VIEWERS_GROUP$$']},
                       'kind': 'osdu:osdu:UnitQuantity:1.0.0', 'id': '',
                       'data': {'id': '$$srn:NAMESPACE$$:reference-data/UnitQuantity:1',
                                'groupType': 'reference-data',
                                'resourceObjectCreationDateTime': '2020-10-08T12:16:15Z',
                                'resourceVersionCreationDateTime': '2020-10-08T12:16:15Z',
                                'source': 'Workbook Authoring/UnitQuantity.1.0.0.xlsx; commit SHA 3159b9b1.',
                                'Name': 'dimensionless', 'ID': '1', 'InactiveIndicator': False,
                                'Code': '1', 'AttributionAuthority': 'Energistics',
                                'AttributionPublication': 'Energistics Unit of Measure Dictionary V1.0',
                                'AttributionRevision': '1.0', 'BaseForConversion': 'Euc',
                                'ParentUnitQuantity': '1',
                                'PersistableReference': '{"ancestry":"1","type":"UM"}',
                                'UnitDimension': '1'}}]

PROCESS_FILE_ITEMS_RESULT = (
    [
        (
            {
                'kind': 'test:osdu:file:3.0.0',
                'legal': {'legaltags': ['odes-demo-legaltag'], 'otherRelevantDataCountries': ['US'],
                          'status': 'compliant'},
                'acl': {'viewers': ['data.default.viewers@odes.osdu.test.net'],
                        'owners': ['data.default.owners@odes.osdu.test.net']},
                'data': {
                    'ResourceTypeID': 'srn:type:file/las2:',
                    'ResourceSecurityClassification': 'srn:reference-data/ResourceSecurityClassification:RESTRICTED:',
                    'Data': {'GroupTypeProperties': {'FileSource': '', 'PreLoadFilePath': 'foo'},
                             'IndividualTypeProperties': {}, 'ExtensionProperties': {}},
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
