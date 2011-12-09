/*

SQL for creating a database VIEW for the unmanaged `Post` model

Tested with: SQLite3

*/

CREATE VIEW askbot_post AS

SELECT
    answer.id + 1000000 AS id,   -- fake unique ID

    /* Some required pseudo-fields */
    "answer" AS post_type,

    joined_question.id AS parent_id,
    joined_question.thread_id AS thread_id,

    answer.id AS self_answer_id,
    NULL AS self_question_id,

    /* Shared fields from content.Content */
    answer.author_id,
    answer.added_at,

    answer.deleted,
    answer.deleted_at,
    answer.deleted_by_id,

    answer.wiki,
    answer.wikified_at,

    answer.locked,
    answer.locked_by_id,
    answer.locked_at,

    answer.score,
    answer.vote_up_count,
    answer.vote_down_count,

    answer.comment_count,
    answer.offensive_flag_count,

    answer.last_edited_at,
    answer.last_edited_by_id,

    answer.html,
    answer.text,

    answer.summary,

    answer.is_anonymous

FROM answer

INNER JOIN question as joined_question
ON joined_question.id=answer.question_id

UNION

SELECT
    question.id AS id,   -- fake unique ID

    /* Some required pseudo-fields */
    "question" AS post_type,

    NULL AS parent_id,
    thread_id,

    NULL AS self_answer_id,
    id AS self_question_id,

    /* Shared fields from content.Content */
    author_id,
    added_at,

    deleted,
    deleted_at,
    deleted_by_id,

    wiki,
    wikified_at,

    locked,
    locked_by_id,
    locked_at,

    score,
    vote_up_count,
    vote_down_count,

    comment_count,
    offensive_flag_count,

    last_edited_at,
    last_edited_by_id,

    html,
    text,

    summary,

    is_anonymous


FROM question;