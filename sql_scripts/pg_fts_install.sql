ALTER TABLE question ADD COLUMN tsv tsvector;

CREATE OR REPLACE FUNCTION public.create_plpgsql_language ()
    RETURNS TEXT
    AS $$
        CREATE LANGUAGE plpgsql;
        SELECT 'language plpgsql created'::TEXT;
    $$
LANGUAGE 'sql';

SELECT CASE WHEN
      (SELECT true::BOOLEAN
         FROM pg_language
        WHERE lanname='plpgsql')
    THEN
      (SELECT 'language already installed'::TEXT)
    ELSE
      (SELECT public.create_plpgsql_language())
    END;

DROP FUNCTION public.create_plpgsql_language ();

CREATE OR REPLACE FUNCTION set_question_tsv() RETURNS TRIGGER AS $$
begin
  new.tsv :=
     setweight(to_tsvector('english', coalesce(new.tagnames,'')), 'A') ||
     setweight(to_tsvector('english', coalesce(new.title,'')), 'B') ||
     setweight(to_tsvector('english', coalesce(new.summary,'')), 'C');
  RETURN new;
end
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
ON question FOR EACH ROW EXECUTE PROCEDURE set_question_tsv();

CREATE INDEX blog_entry_tsv ON blog_entry USING gin(body_tsv);

UPDATE question SET title = title;

SELECT (ts_rank(p.factors, tsv, p.query)) AS "ranking", "question"."id", "question"."title",
"question"."author_id", "question"."added_at", "question"."wiki", "question"."wikified_at", "question"."answer_accepted", "question"."closed", "question"."closed_by_id", "question"."closed_at", "question"."close_reason", "question"."deleted", "question"."deleted_at", "question"."deleted_by_id", "question"."locked", "question"."locked_by_id", "question"."locked_at", "question"."score", "question"."vote_up_count", "question"."vote_down_count", "question"."answer_count", "question"."comment_count", "question"."view_count", "question"."offensive_flag_count", "question"."favourite_count", "question"."last_edited_at", "question"."last_edited_by_id", "question"."last_activity_at", "question"."last_activity_by_id", "question"."tagnames", "question"."summary", "question"."html" FROM "question" , "(SELECT '{0.2, 0.5, 0.75, 1.0}'::float4[] AS factors, plainto_tsquery(false) AS query) p" WHERE "question"."deleted" = E'robots'  AND tsv @@ p.query ORDER BY "ranking" DESC LIMIT 21  