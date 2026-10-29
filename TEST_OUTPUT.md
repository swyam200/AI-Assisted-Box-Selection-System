# Automated Test Run Output

This document contains the verified terminal test output produced by running the full test suite via Django's test runner:

```bash
python manage.py test -v 2
```

---

## Execution Log

```text
Found 19 test(s).
Operations to perform:
  Synchronize unmigrated apps: messages, rest_framework, staticfiles
  Apply all migrations: admin, auth, box_selection, contenttypes, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying box_selection.0001_initial... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).

Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...

test_fragile_warning_generated (box_selection.tests.AIPackingAssistantTests.test_fragile_warning_generated) ... ok
test_heavy_load_h_taping_advice (box_selection.tests.AIPackingAssistantTests.test_heavy_load_h_taping_advice) ... ok
test_3d_spatial_collision_detection (box_selection.tests.BoxPacker3DTests.test_3d_spatial_collision_detection) ... ok
test_item_rotation_allows_fit (box_selection.tests.BoxPacker3DTests.test_item_rotation_allows_fit) ... ok
test_rotation_restriction_fails_when_disallowed (box_selection.tests.BoxPacker3DTests.test_rotation_restriction_fails_when_disallowed) ... ok
test_single_item_fits_exact_or_smaller_box (box_selection.tests.BoxPacker3DTests.test_single_item_fits_exact_or_smaller_box) ... ok
test_volume_exceeded_disqualifies_box (box_selection.tests.BoxPacker3DTests.test_volume_exceeded_disqualifies_box) ... ok
test_weight_capacity_exceeded_disqualifies_box (box_selection.tests.BoxPacker3DTests.test_weight_capacity_exceeded_disqualifies_box) ... ok
test_multi_box_partition_when_no_single_box_fits (box_selection.tests.BoxRecommenderServiceTests.test_multi_box_partition_when_no_single_box_fits) ... ok
test_recommends_lowest_cost_fitting_box (box_selection.tests.BoxRecommenderServiceTests.test_recommends_lowest_cost_fitting_box) ... ok
test_size_constraint_promotes_to_larger_box (box_selection.tests.BoxRecommenderServiceTests.test_size_constraint_promotes_to_larger_box) ... ok
test_weight_disqualification_in_recommender (box_selection.tests.BoxRecommenderServiceTests.test_weight_disqualification_in_recommender) ... ok
test_recommend_api_validation_error_empty_payload (box_selection.tests.BoxSelectionAPITests.test_recommend_api_validation_error_empty_payload) ... ok
test_recommend_api_with_custom_items (box_selection.tests.BoxSelectionAPITests.test_recommend_api_with_custom_items) ... ok
test_recommend_api_with_order_id (box_selection.tests.BoxSelectionAPITests.test_recommend_api_with_order_id) ... ok
test_box_catalog_view_loads (box_selection.tests.WebViewsTests.test_box_catalog_view_loads) ... ok
test_dashboard_view_loads (box_selection.tests.WebViewsTests.test_dashboard_view_loads) ... ok
test_simulator_get_loads (box_selection.tests.WebViewsTests.test_simulator_get_loads) ... ok
test_simulator_post_calculation (box_selection.tests.WebViewsTests.test_simulator_post_calculation) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.200s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```

---

## Test Coverage Summary

| Test Group | Test Case Count | Status | Description |
| :--- | :---: | :---: | :--- |
| **3D Packing Engine (`BoxPacker3D`)** | 6 | **PASS** | Tests single item bounding, 6-DOF 3D coordinate rotation, yaw-only rotation restriction, weight ceiling disqualification, volume overflow, and 3D cuboid collision overlap detection. |
| **Recommendation & Cost Optimization (`BoxRecommenderService`)** | 4 | **PASS** | Tests lowest-cost box selection among candidates, dimension promotion to larger box, heavy item rejection with diagnostic logging, and multi-box greedy partition fallback. |
| **AI Packaging Assistant (`AIPackingAssistant`)** | 2 | **PASS** | Tests fragile item identification & warning tape instructions, and heavy load identification requiring fiberglass H-taping. |
| **REST API (`/api/recommend/`)** | 3 | **PASS** | Tests JSON requests with custom items, order ID lookups with database history tracking, and validation error responses on malformed payloads. |
| **Web UI Views** | 4 | **PASS** | Tests Dashboard, Interactive Simulator (GET/POST), and Box Catalog views rendering with HTTP 200. |
| **Total** | **19** | **100% PASS** | Zero failures, zero errors, fast execution (0.2s). |
