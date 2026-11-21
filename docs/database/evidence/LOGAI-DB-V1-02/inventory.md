# Complete Keycloak reference inventory

Generated from catalogue.json; every row is included in keycloak-db.mmd.
Full columns, defaults, ordered key groups and index definitions: catalogue.json / reference-schema.sql.
Historical changelog operations per entity: table-sources.json (final state comes from catalogue).

| Section | Table | Columns | PK columns | Extra UNIQUE groups | FKs | Indexes |
| --- | --- | ---: | --- | --- | ---: | ---: |
| Authentication flows and required actions | `authentication_execution` | 10 | id | none | 2 | 3 |
| Authentication flows and required actions | `authentication_flow` | 7 | id | none | 1 | 2 |
| Authentication flows and required actions | `authenticator_config` | 3 | id | none | 1 | 2 |
| Authentication flows and required actions | `authenticator_config_entry` | 3 | authenticator_id,name | none | 0 | 1 |
| Authentication flows and required actions | `required_action_config` | 3 | required_action_id,name | none | 0 | 1 |
| Authentication flows and required actions | `required_action_provider` | 8 | id | none | 1 | 2 |
| Authorization services | `associated_policy` | 2 | policy_id,associated_policy_id | none | 2 | 2 |
| Authorization services | `policy_config` | 3 | policy_id,name | none | 1 | 1 |
| Authorization services | `resource_attribute` | 4 | id | none | 1 | 1 |
| Authorization services | `resource_policy` | 2 | resource_id,policy_id | none | 2 | 2 |
| Authorization services | `resource_scope` | 2 | resource_id,scope_id | none | 2 | 2 |
| Authorization services | `resource_server` | 4 | id | none | 0 | 1 |
| Authorization services | `resource_server_perm_ticket` | 9 | id | (owner,requester,resource_server_id,resource_id,scope_id) | 4 | 4 |
| Authorization services | `resource_server_policy` | 8 | id | (name,resource_server_id) | 1 | 3 |
| Authorization services | `resource_server_resource` | 8 | id | (name,owner,resource_server_id) | 1 | 3 |
| Authorization services | `resource_server_scope` | 5 | id | (name,resource_server_id) | 1 | 3 |
| Authorization services | `resource_uris` | 2 | resource_id,value | none | 1 | 1 |
| Authorization services | `scope_policy` | 2 | scope_id,policy_id | none | 2 | 2 |
| Clients and client scopes | `client` | 26 | id | (realm_id,client_id) | 0 | 3 |
| Clients and client scopes | `client_attributes` | 3 | client_id,name | none | 1 | 2 |
| Clients and client scopes | `client_auth_flow_bindings` | 3 | client_id,binding_name | none | 0 | 1 |
| Clients and client scopes | `client_initial_access` | 6 | id | none | 1 | 2 |
| Clients and client scopes | `client_node_registrations` | 3 | client_id,name | none | 1 | 1 |
| Clients and client scopes | `client_scope` | 5 | id | (realm_id,name) | 0 | 3 |
| Clients and client scopes | `client_scope_attributes` | 3 | scope_id,name | none | 1 | 2 |
| Clients and client scopes | `client_scope_client` | 3 | client_id,scope_id | none | 0 | 3 |
| Clients and client scopes | `client_scope_role_mapping` | 2 | scope_id,role_id | none | 1 | 3 |
| Clients and client scopes | `default_client_scope` | 3 | realm_id,scope_id | none | 1 | 3 |
| Clients and client scopes | `protocol_mapper` | 6 | id | none | 2 | 3 |
| Clients and client scopes | `protocol_mapper_config` | 3 | protocol_mapper_id,name | none | 1 | 1 |
| Clients and client scopes | `redirect_uris` | 2 | client_id,value | none | 1 | 2 |
| Clients and client scopes | `scope_mapping` | 2 | client_id,role_id | none | 1 | 2 |
| Clients and client scopes | `web_origins` | 2 | client_id,value | none | 1 | 2 |
| Identity brokering and federation | `broker_link` | 7 | identity_provider,user_id | none | 0 | 1 |
| Identity brokering and federation | `fed_user_attribute` | 9 | id | none | 0 | 4 |
| Identity brokering and federation | `fed_user_consent` | 9 | id | none | 0 | 4 |
| Identity brokering and federation | `fed_user_consent_cl_scope` | 2 | user_consent_id,scope_id | none | 0 | 1 |
| Identity brokering and federation | `fed_user_credential` | 11 | id | none | 0 | 3 |
| Identity brokering and federation | `fed_user_group_membership` | 4 | group_id,user_id | none | 0 | 3 |
| Identity brokering and federation | `fed_user_required_action` | 4 | required_action,user_id | none | 0 | 3 |
| Identity brokering and federation | `fed_user_role_mapping` | 4 | role_id,user_id | none | 0 | 3 |
| Identity brokering and federation | `federated_identity` | 6 | identity_provider,user_id | none | 1 | 3 |
| Identity brokering and federation | `federated_user` | 3 | id | none | 0 | 1 |
| Identity brokering and federation | `identity_provider` | 15 | internal_id | (provider_alias,realm_id) | 1 | 5 |
| Identity brokering and federation | `identity_provider_config` | 3 | identity_provider_id,name | none | 1 | 1 |
| Identity brokering and federation | `identity_provider_mapper` | 5 | id | none | 1 | 2 |
| Identity brokering and federation | `idp_mapper_config` | 3 | idp_mapper_id,name | none | 1 | 1 |
| Identity brokering and federation | `user_federation_config` | 3 | user_federation_provider_id,name | none | 1 | 1 |
| Identity brokering and federation | `user_federation_mapper` | 5 | id | none | 2 | 3 |
| Identity brokering and federation | `user_federation_mapper_config` | 3 | user_federation_mapper_id,name | none | 1 | 1 |
| Identity brokering and federation | `user_federation_provider` | 8 | id | none | 1 | 2 |
| Migration bookkeeping (Keycloak and Liquibase owned) | `databasechangelog` | 14 | none | none | 0 | 0 |
| Migration bookkeeping (Keycloak and Liquibase owned) | `databasechangeloglock` | 4 | id | none | 0 | 1 |
| Migration bookkeeping (Keycloak and Liquibase owned) | `migration_model` | 3 | id | none | 0 | 2 |
| Realms, components and organizations | `component` | 7 | id | none | 1 | 3 |
| Realms, components and organizations | `component_config` | 4 | id | none | 1 | 2 |
| Realms, components and organizations | `org` | 8 | id | (realm_id,alias); (group_id); (realm_id,name) | 0 | 4 |
| Realms, components and organizations | `org_domain` | 4 | id,name | none | 0 | 2 |
| Realms, components and organizations | `realm` | 53 | id | (name) | 0 | 3 |
| Realms, components and organizations | `realm_attribute` | 3 | name,realm_id | none | 1 | 2 |
| Realms, components and organizations | `realm_default_groups` | 2 | realm_id,group_id | (group_id) | 1 | 3 |
| Realms, components and organizations | `realm_enabled_event_types` | 2 | realm_id,value | none | 1 | 2 |
| Realms, components and organizations | `realm_events_listeners` | 2 | realm_id,value | none | 1 | 2 |
| Realms, components and organizations | `realm_localizations` | 3 | realm_id,locale | none | 0 | 1 |
| Realms, components and organizations | `realm_required_credential` | 5 | realm_id,type | none | 1 | 1 |
| Realms, components and organizations | `realm_smtp_config` | 3 | realm_id,name | none | 1 | 1 |
| Realms, components and organizations | `realm_supported_locales` | 2 | realm_id,value | none | 1 | 2 |
| Sessions and events | `admin_event_entity` | 13 | id | none | 0 | 2 |
| Sessions and events | `event_entity` | 11 | id | none | 0 | 2 |
| Sessions and events | `offline_client_session` | 8 | user_session_id,client_id,client_storage_provider,external_client_id,offline_flag | none | 0 | 1 |
| Sessions and events | `offline_user_session` | 9 | user_session_id,offline_flag | none | 0 | 4 |
| Sessions and events | `revoked_token` | 2 | id | none | 0 | 2 |
| Sessions and events | `username_login_failure` | 6 | realm_id,username | none | 0 | 1 |
| Users, groups, roles and credentials | `composite_role` | 2 | composite,child_role | none | 2 | 3 |
| Users, groups, roles and credentials | `credential` | 9 | id | none | 1 | 2 |
| Users, groups, roles and credentials | `group_attribute` | 4 | id | none | 1 | 3 |
| Users, groups, roles and credentials | `group_role_mapping` | 2 | role_id,group_id | none | 1 | 2 |
| Users, groups, roles and credentials | `keycloak_group` | 5 | id | (realm_id,parent_group,name) | 0 | 2 |
| Users, groups, roles and credentials | `keycloak_role` | 8 | id | (name,client_realm_constraint) | 1 | 4 |
| Users, groups, roles and credentials | `role_attribute` | 4 | id | none | 1 | 2 |
| Users, groups, roles and credentials | `user_attribute` | 7 | id | none | 1 | 5 |
| Users, groups, roles and credentials | `user_consent` | 7 | id | (client_storage_provider,external_client_id,user_id); (client_id,user_id) | 1 | 4 |
| Users, groups, roles and credentials | `user_consent_client_scope` | 2 | user_consent_id,scope_id | none | 1 | 3 |
| Users, groups, roles and credentials | `user_entity` | 13 | id | (realm_id,email_constraint); (realm_id,username) | 0 | 5 |
| Users, groups, roles and credentials | `user_group_membership` | 3 | group_id,user_id | none | 1 | 2 |
| Users, groups, roles and credentials | `user_required_action` | 2 | required_action,user_id | none | 1 | 2 |
| Users, groups, roles and credentials | `user_role_mapping` | 2 | role_id,user_id | none | 1 | 2 |
