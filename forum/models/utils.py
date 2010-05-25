from forum import const
#from forum.models import Comment, Question, Answer
#from forum.models import QuestionRevision, AnswerRevision
from forum.models import Activity, User

#todo: don't like that this file deals with models directly
def _make_mention(mentioned_whom, context_object = None):
    mentioned_by = context_object.get_last_author()
    if mentioned_whom:
        if mentioned_whom != mentioned_by:
            m = Activity.objects.create_new_mention(
                    mentioned_by = mentioned_by,
                    mentioned_whom = mentioned_whom,
                    mentioned_in = context_object
                )
        url = mentioned_whom.get_profile_url()
        username = mentioned_whom.username
        return '<a href="%s">@%s</a>' % (url, username)
    else:
        return '@'

def _extract_matching_mentioned_author(text, authors):

    if len(text) == 0:
        return None, ''

    for a in authors:
        if text.startswith(a.username):
            ulen = len(a.username)
            if len(text) == ulen:
                text = ''
            elif text[ulen] in const.TWITTER_STYLE_MENTION_TERMINATION_CHARS:
                text = text[ulen:]
            else:
                #near miss, here we could insert a warning that perhaps
                #a termination character is needed
                continue
            return a, text
    return None, text

def mentionize(text, context_object = None):

    if '@' not in text:
        return text

    op = context_object.get_origin_post()
    authors = op.get_author_list( include_comments = True, recursive = True )

    text_copy = text
    extra_name_seeds = set()
    while '@' in text_copy:
        pos = text_copy.index('@')
        text_copy = text_copy[pos+1:]#chop off prefix
        name_seed = ''
        for c in text_copy:
            if c in const.TWITTER_STYLE_MENTION_TERMINATION_CHARS:
                extra_name_seeds.add(name_seed)
                break
            if len(name_seed) > 10:
                extra_name_seeds.add(name_seed)
                break
            if c == '@':
                extra_name_seeds.add(name_seed)
                break
            name_seed += c

    extra_authors = set()
    for name_seed in extra_name_seeds:
        if len(name_seed) > 0:
            extra_authors.update(User.objects.filter(username__startswith = name_seed))

    authors += list(extra_authors)

    output = ''
    while '@' in text:
        #the purpose of this loop is to convert any occurance of '@mention ' syntax
        #to user account links leading space is required unless @ is the first 
        #character in whole text, also, either a punctuation or a ' ' char is required
        #after the name
        pos = text.index('@')

        #save stuff before @mention to the output
        output += text[:pos]#this works for pos == 0 too

        if len(text) == pos + 1:
            #finish up if the found @ is the last symbol
            output += '@'
            text = ''
            break

        if pos > 0:

            if text[pos-1] in const.TWITTER_STYLE_MENTION_TERMINATION_CHARS:
                #if there is a termination character before @mention
                #indeed try to find a matching person
                text = text[pos+1:]
                matching_author, text = _extract_matching_mentioned_author(text, authors)
                output += _make_mention(matching_author, context_object = context_object)

            else:
                #if there isn't, i.e. text goes like something@mention, do not look up people
                output += '@'
                text = text[pos+1:]
        else:
            #do this if @ is the first character
            text = text[1:]
            matching_author, text = _extract_matching_mentioned_author(text, authors)
            output += _make_mention(matching_author, context_object = context_object)

    #append the rest of text that did not have @ symbols
    output += text
    return output

