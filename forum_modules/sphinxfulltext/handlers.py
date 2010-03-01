from forum.models import Question

def question_search(keywords, orderby):
    return Question.search.query(keywords)