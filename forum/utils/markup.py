from forum import const
#from forum.models import Comment, Question, Answer
#from forum.models import QuestionRevision, AnswerRevision
from forum.models import Mention, User

def _make_mention(mentioned_whom, context_object = None):
    mentioned_by = context_object.get_last_author()
    if mentioned_whom:
        if mentioned_whom != mentioned_by:
            m = Mention(
                    mentioned_by = mentioned_by,
                    mentioned_whom = mentioned_whom,
                    content_object = context_object
                )
            m.save()
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
    authors = list(op.get_all_authors())

    extra_name_seed = ''
    for c in text:
        if c in const.TWITTER_STYLE_MENTION_TERMINATION_CHARS:
            break
        else:
            extra_name_seed += c
        if len(extra_name_seed) > 10:
            break

    if len(extra_name_seed) > 0:
        authors += list(User.objects.filter(username__startswith = extra_name_seed))

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

