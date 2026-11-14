-- Metadata only. No reads from Keycloak domain tables or Liquibase history rows.
-- Run against an isolated reference or an explicitly authorised read-only target.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT jsonb_pretty(jsonb_build_object(
 'postgres_version', current_setting('server_version'),
 'schema', 'public',
 'user_types', ARRAY(SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
   WHERE n.nspname='public' AND t.typtype IN ('e','d','r','m','b') AND t.typelem=0
   ORDER BY t.typname),
 'tables', (SELECT jsonb_agg(jsonb_build_object(
   'name', t.relname,
   'columns', (SELECT jsonb_agg(jsonb_build_object(
     'name', a.attname, 'position', a.attnum,
     'type', format_type(a.atttypid,a.atttypmod),
     'nullable', NOT a.attnotnull,
     'default', pg_get_expr(d.adbin,d.adrelid),
     'identity', a.attidentity, 'generated', a.attgenerated
   ) ORDER BY a.attnum) FROM pg_attribute a
   LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
   WHERE a.attrelid=t.oid AND a.attnum>0 AND NOT a.attisdropped),
   'constraints', COALESCE((SELECT jsonb_agg(jsonb_build_object(
     'name', c.conname, 'kind', c.contype,
     'columns', ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(n,pos)
        JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.n ORDER BY k.pos),
     'referenced_table', CASE WHEN c.contype='f' THEN c.confrelid::regclass::text END,
     'referenced_columns', CASE WHEN c.contype='f' THEN ARRAY(
        SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(n,pos)
        JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.n ORDER BY k.pos) END,
     'definition', pg_get_constraintdef(c.oid,true),
     'deferrable', c.condeferrable, 'initially_deferred', c.condeferred,
     'validated', c.convalidated
   ) ORDER BY c.conname) FROM pg_constraint c WHERE c.conrelid=t.oid),'[]'::jsonb),
   'indexes', COALESCE((SELECT jsonb_agg(jsonb_build_object(
     'name', ic.relname, 'unique', ix.indisunique, 'primary', ix.indisprimary,
     'valid', ix.indisvalid, 'definition', pg_get_indexdef(ix.indexrelid),
     'predicate', pg_get_expr(ix.indpred,ix.indrelid),
     'expressions', pg_get_expr(ix.indexprs,ix.indrelid),
     'key_columns', ARRAY(SELECT a.attname FROM unnest(ix.indkey) WITH ORDINALITY k(n,pos)
       JOIN pg_attribute a ON a.attrelid=ix.indrelid AND a.attnum=k.n
       WHERE k.pos<=ix.indnkeyatts ORDER BY k.pos)
   ) ORDER BY ic.relname) FROM pg_index ix JOIN pg_class ic ON ic.oid=ix.indexrelid
   WHERE ix.indrelid=t.oid),'[]'::jsonb)
 ) ORDER BY t.relname) FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace
   WHERE n.nspname='public' AND t.relkind IN ('r','p')),
 'sequences', COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'name', c.relname, 'type', format_type(s.seqtypid,NULL),
    'start', s.seqstart, 'increment', s.seqincrement, 'minimum', s.seqmin,
    'maximum', s.seqmax, 'cache', s.seqcache, 'cycle', s.seqcycle
 ) ORDER BY c.relname) FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'),'[]'::jsonb),
 'views', ARRAY(SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind IN ('v','m') ORDER BY c.relname),
 'triggers', ARRAY(SELECT tr.tgname FROM pg_trigger tr JOIN pg_class c ON c.oid=tr.tgrelid
    JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT tr.tgisinternal
    ORDER BY tr.tgname)
));
COMMIT;
