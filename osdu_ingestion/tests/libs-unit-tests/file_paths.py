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

DATA_PATH_PREFIX = f"{os.path.dirname(__file__)}/data"

MANIFEST_REFERENCE_PATTERNS_WHITELIST = f"{DATA_PATH_PREFIX}/reference_patterns_whitelist.txt"

MANIFEST_GENERIC_SCHEMA_PATH = f"{DATA_PATH_PREFIX}/manifests/schema_Manifest.1.0.0.json"
MANIFEST_BATCH_SAVE_PATH = f"{DATA_PATH_PREFIX}/manifests/batch_save_Manifest.json"
MANIFEST_NEW_GENERIC_SCHEMA_PATH = f"{DATA_PATH_PREFIX}/manifests/new_schema_Manifest.1.0.0.json"
MANIFEST_GENERIC_PATH = f"{DATA_PATH_PREFIX}/manifests/Manifest.1.0.0.json"

MANIFEST_WELLBORE_VALID_PATH = f"{DATA_PATH_PREFIX}/master/Wellbore.0.3.0.json"
MANIFEST_BATCH_WELLBORE_VALID_PATH = f"{DATA_PATH_PREFIX}/master/batch_Wellbore.0.3.0.json"
SCHEMA_WELLBORE_VALID_PATH = f"{DATA_PATH_PREFIX}/master/schema_Wellbore.3.0.0.json"
RECORD_WELLBORE_VALID_PATH = f"{DATA_PATH_PREFIX}/master/record_Wellbore.0.3.0.json"
SCHEMA_GENERIC_MASTERDATA_PATH = f"{DATA_PATH_PREFIX}/master/schema_GenericMasterData.1.0.0.json"
SCHEMA_TEST_MASTERDATA_PATH = f"{DATA_PATH_PREFIX}/master/schema_TestMaster.json"
TRAVERSAL_WELLBORE_VALID_PATH = f"{DATA_PATH_PREFIX}/master/traversal_Wellbore.0.3.0.json"

MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/SeismicTraceData.json"
TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/traversal_SeismicTraceData.1.0.0.json"
SCHEMA_FILE_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/schema_File.1.0.0.json"
SCHEMA_WORK_PRODUCT_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/schema_WorkProduct.1.0.0.json"
SCHEMA_SEISMIC_TRACE_DATA_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/schema_SeismicTraceData.1.0.0.json"
RECORD_SEISMIC_TRACE_DATA_VALID_PATH = f"{DATA_PATH_PREFIX}/workProduct/record_SeismicTraceData.json"

SURROGATE_MANIFEST_WELLBORE = f"{DATA_PATH_PREFIX}/surrogate/Wellbore.0.3.0.json"

MANIFEST_EMPTY_PATH = f"{DATA_PATH_PREFIX}/invalid/EmptyManifest.json"
TRAVERSAL_MANIFEST_EMPTY_PATH = f"{DATA_PATH_PREFIX}/invalid/TraversalEmptyManifest.json"

SEARCH_VALID_RESPONSE_PATH = f"{DATA_PATH_PREFIX}/other/SearchResponseValid.json"
SEARCH_INVALID_RESPONSE_PATH = f"{DATA_PATH_PREFIX}/other/SearchResponseInvalid.json"
SEARCH_VALID_OFFSET_RESPONSE_PATH = f"{DATA_PATH_PREFIX}/other/SearchResponseForOffsetValid.json"
SEARCH_EXTRACTED_IDS_PATH = f"{DATA_PATH_PREFIX}/other/ExtractedIds.json"

SURROGATE_MANIFEST_WELLBORE = f"{DATA_PATH_PREFIX}/surrogate/Wellbore.0.3.0.json"

MANIFEST_WELL_PATH = f"{DATA_PATH_PREFIX}/master/r3_Well.json"
TRAVERSAL_WELL_PATH = f"{DATA_PATH_PREFIX}/master/traversal_r3_Well.json"
REF_RESULT_WELL_PATH = f"{DATA_PATH_PREFIX}/master/ref_result_r3_Well.json"


MANIFEST_WELLLOG_PATH = f"{DATA_PATH_PREFIX}/workProduct/r3_Welllog.json"
TRAVERSAL_WELLLOG_PATH = f"{DATA_PATH_PREFIX}/workProduct/traversal_r3_Welllog.json"
REF_RESULT_WELLLOG_PATH = f"{DATA_PATH_PREFIX}/workProduct/ref_result_r3_Welllog.json"
REF_RESULT_WHITELIST_WELLLOG_PATH = f"{DATA_PATH_PREFIX}/workProduct/ref_result_whitelist_r3_Welllog.json"
BATCH_MANIFEST_WELLBORE = f"{DATA_PATH_PREFIX}/batchManifest/Wellbore.0.3.0.json"

DATA_INTEGRITY_VALID_DATA = f"{DATA_PATH_PREFIX}/data_integrity/valid_data.json"
DATA_INTEGRITY_ORPHAN_DATASETS = f"{DATA_PATH_PREFIX}/data_integrity/orphan_datasets.json"
DATA_INTEGRITY_VALID_WP_INVALID_WPC = f"{DATA_PATH_PREFIX}/data_integrity/valid_wp_invalid_wpc.json"
DATA_INTEGRITY_INVALID_WP = f"{DATA_PATH_PREFIX}/data_integrity/invalid_wp.json"
DATA_INTEGRITY_EMPTY_DATA = f"{DATA_PATH_PREFIX}/data_integrity/empty_data.json"
DATA_INTEGRITY_EMPTY_DATA_CASE_2 = f"{DATA_PATH_PREFIX}/data_integrity/empty_data_inside.json"
DATA_INTEGRITY_EMPTY_WP = f"{DATA_PATH_PREFIX}/data_integrity/empty_wp.json"
DATA_INTEGRITY_VALID_REAL_IDS = f"{DATA_PATH_PREFIX}/data_integrity/valid_data_real_ids.json"
DATA_INTEGRITY_VALID_DATA_IDS_WITH_COLON = f"{DATA_PATH_PREFIX}/data_integrity/valid_data_ids_with_colon.json"

FILES_SOURCE_VALID = f"{DATA_PATH_PREFIX}/data_integrity/file_source/valid_files.json"
FILES_SOURCE_INVALID = f"{DATA_PATH_PREFIX}/data_integrity/file_source/invalid_files.json"
FILE_COLLECTIONS_VALID = f"{DATA_PATH_PREFIX}/data_integrity/file_source/valid_file_collections.json"
FILE_COLLECTIONS_INVALID = f"{DATA_PATH_PREFIX}/data_integrity/file_source/invalid_file_collections.json"

SCHEMA_WPC_DATA_QUALITY = f"{DATA_PATH_PREFIX}/surrogate/schemas/DataQuality.1.0.0.json"
SCHEMA_WORK_PRODUCT = f"{DATA_PATH_PREFIX}/surrogate/schemas/WorkProduct.1.0.0.json"
SURROGATE_WPC_DATA_QUALITY = f"{DATA_PATH_PREFIX}/surrogate/manifests/DataQuality.1.0.0.json"
SURROGATE_WORK_PRODUCT = f"{DATA_PATH_PREFIX}/surrogate/manifests/WorkProduct.1.0.0.json"
SURROGATE_MANIFEST_SEISMIC_NO_REFS_PATH= f"{DATA_PATH_PREFIX}/surrogate/manifests/SeismicTraceData.1.0.0_with_no_refs.json"

FILE_GENERIC_WRONG_DATE_TIME = f"{DATA_PATH_PREFIX}/datasets/File.Generic.1.0.0_wrong_date_time.json"
SCHEMA_FILE_GENERIC = f"{DATA_PATH_PREFIX}/datasets/schema_File.Generic.1.0.0.json"
