CREATE OR REPLACE FUNCTION column_exists(colname text, tablename text)
RETURNS boolean AS
$$
DECLARE
    q text;
    onerow record;
BEGIN
q = `SELECT attname FROM pg_attribute WHERE attrelid = ( SELECT oid FROM pg_class WHERE relname = '''||tablename||''') AND attname = '''||colname||''' `;

END
$$
LANGUAGE plpgsql

CREATE OR REPLACE FUNCTION
