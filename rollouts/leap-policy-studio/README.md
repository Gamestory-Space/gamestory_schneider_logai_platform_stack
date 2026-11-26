# Policy Studio Stage 1 platform compatibility

This folder contains role preparation and read-only verification for the V012 candidate. The existing
Ping release and packaged V011 rollout remain pinned to their published images.

The candidate API is the source of Flyway migrations. Use its exact V012 image or
reviewed migration bundle with the existing dedicated migration role. An established
V011 schema must have validated Flyway history before applying V012. Preserve the
migration schema name and existing role grants. The V012 rename keeps relation OIDs,
and its catalogue receives read access for explicit readers of the policy table.
A fresh schema needs role provisioning for the new names before runtime validation.
The adjacent `grant-runtime.psql` uses the existing runtime role and grants SELECT
only on the engineering-owned catalogue. Run the grant script as the migration
owner in an approved rehearsal, supplying the same target parameters plus
`-v runtime_role=REHEARSAL_ROLE`.

After an approved rehearsal migration and role setup, run the read-only check with
the actual API runtime credentials and search path:

```sh
psql -X -v ON_ERROR_STOP=1 -v expected_database=REHEARSAL_DB \
  -v target_schema=public -f rollouts/leap-policy-studio/runtime-check.psql
```

V011 API pods and V012 table names require a coordinated change window. Stage 1
snapshots are review-only. No chart values, image pins, rollout flags or client
configuration are changed by these assets.
