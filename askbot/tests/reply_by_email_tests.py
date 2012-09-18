from django.utils.translation import ugettext as _
from askbot.models import ReplyAddress
from askbot.mail.lamson_handlers import PROCESS, VALIDATE_EMAIL, get_parts
from askbot.mail import extract_user_signature
from askbot import const


from askbot.tests.utils import AskbotTestCase
from askbot.models import Post, PostRevision

TEST_CONTENT = 'Test content'
TEST_LONG_CONTENT = 'Test content' * 10

class MockPart(object):
    def __init__(self, body, content_type='text/plain'):
        self.body = body
        self.content_encoding = {'Content-Type':(content_type,)}

class MockMessage(dict):

    def __init__(
        self, content, from_email, signature = '', response_code = False
    ):
        self.From= from_email
        self['Subject'] = 'test subject'

        if response_code != False:
            #in this case we modify the content
            re_separator = const.REPLY_SEPARATOR_TEMPLATE % {
                                    'user_action': 'john did something',
                                    'instruction': 'reply above this line'
                                }
            content += '\n\n\nToday someone wrote:\n' + re_separator + \
                '\nblah blah\n' + response_code + '\n' + signature

        self._body = content
        self._part = MockPart(content)
        self._alternatives = []

    def body(self):
        return self._body

    def attach_alternative(self, content, content_type):
        assert content is not None
        assert content_type is not None
        self._alternatives.append(MockPart(content, content_type))

    def walk(self):
        """todo: add real file attachment"""
        return [self._part] + self._alternatives

class ReplyAddressModelTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u1.set_status('a')
        self.u1.email = "user1@domain.com"
        self.u1.save()

        self.u1.moderate_user_reputation(self.u1, reputation_change = 100, comment=  "no comment")
        self.u2 = self.create_user(username='user2')
        self.u1.moderate_user_reputation(self.u2, reputation_change = 100, comment=  "no comment")
        self.u3 = self.create_user(username='user3')
        self.u1.moderate_user_reputation(self.u3, reputation_change = 100, comment=  "no comment")

        self.question = self.post_question(
            user = self.u1,
            follow = True,
        )
        self.answer = self.post_answer(
            user = self.u2,
            question = self.question
        )

        self.comment = self.post_comment(user = self.u2, parent_post = self.answer)

    def test_process_correct_answer_comment(self):
        addr = ReplyAddress.objects.create_new(
                                    post = self.answer,
                                    user = self.u1
                                ).address
        reply_separator = const.REPLY_SEPARATOR_TEMPLATE % {
                                    'user_action': 'john did something',
                                    'instruction': 'reply above this line'
                                }
        msg = MockMessage(
            "This is a test reply \n\nOn such and such someone"
            "wrote something \n\n%s\nlorem ipsum " % (reply_separator),
            "user1@domain.com"
        )
        msg['Subject'] = 'test subject'
        PROCESS(msg, address = addr)
        self.assertEquals(self.answer.comments.count(), 2)
        self.assertEquals(self.answer.comments.all().order_by('-pk')[0].text.strip(), "This is a test reply")

    def test_address_creation(self):
        self.assertEquals(ReplyAddress.objects.all().count(), 0)
        result = ReplyAddress.objects.create_new(
                                        post = self.answer,
                                        user = self.u1
                                    )
        self.assertTrue(len(result.address) >= 12 and len(result.address) <= 25)
        self.assertEquals(ReplyAddress.objects.all().count(), 1)


    def test_create_answer_reply(self):
        result = ReplyAddress.objects.create_new(
                                        post = self.answer,
                                        user = self.u1
                                    )
        post = result.create_reply(TEST_CONTENT)
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, TEST_CONTENT)
        self.assertEquals(self.answer.comments.count(), 2)

    def test_create_comment_reply(self):
        result = ReplyAddress.objects.create_new(
                                        post = self.comment,
                                        user = self.u1
                                    )
        post = result.create_reply(TEST_CONTENT)
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, TEST_CONTENT)
        self.assertEquals(self.answer.comments.count(), 2)


    def test_create_question_comment_reply(self):
        result = ReplyAddress.objects.create_new(
                                        post = self.question,
                                        user = self.u3
                                    )
        post = result.create_reply(TEST_CONTENT)
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, TEST_CONTENT)

    def test_create_question_answer_reply(self):
        result = ReplyAddress.objects.create_new(
                                        post = self.question,
                                        user = self.u3
                                    )
        post = result.create_reply(TEST_LONG_CONTENT)
        self.assertEquals(post.post_type, "answer")
        self.assertEquals(post.text, TEST_LONG_CONTENT)

class EmailSignatureDetectionTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user('user1', status = 'a')
        self.u2 = self.create_user('user2', status = 'a')

    def test_detect_signature_in_response(self):
        question = self.post_question(user = self.u1)

        #create a response address record
        reply_token = ReplyAddress.objects.create_new(
                                        post = question,
                                        user = self.u2,
                                        reply_action = 'post_answer'
                                    )

        self.u2.email_signature = ''
        self.u2.save()

        msg = MockMessage(
                'some text',
                self.u2.email,
                signature = 'Yours Truly',
                response_code = reply_token.address
            )
        PROCESS(msg, address = reply_token.address)

        signature = self.reload_object(self.u2).email_signature
        self.assertEqual(signature, 'Yours Truly')

    def test_detect_signature_in_welcome_response(self):
        reply_token = ReplyAddress.objects.create_new(
                                            user = self.u2,
                                            reply_action = 'validate_email'
                                        )
        self.u2.email_signature = ''
        self.u2.save()

        msg = MockMessage(
                'some text',
                self.u2.email,
                signature = 'Yours Truly',
                response_code = reply_token.address
            )
        VALIDATE_EMAIL(
            msg,
            address = reply_token.address
        )

        signature = self.reload_object(self.u2).email_signature
        self.assertEqual(signature, 'Yours Truly')

class SignatureDetectionTests(AskbotTestCase):
    '''Simple test to detect signature from text'''

    def setUp(self):
        self.u1 = self.create_user('user1', status = 'a')
        self.u1.email_signature = '''--\nFoo Bar'''
        self.u1.save()
        self.plain_text = '''welcome!

On Mon, Sep 17, 2012 at 9:01 AM, <foo@bar.com> wrote:

> **
>         Welcome to Askbot!
>
> Important: *Please reply* to this message, without editing it. We need
> this to determine your email signature and that the email address is valid
> and was typed correctly.
>
> Until we receive the response from you, you will not be able ask or answer
> questions on askbot by email.
>   ------------------------------
>
> Sincerely,
> askbot Administrator
>
> ofqssnfqkvlw
>



--
Foo Bar
'''
        self.html = '''welcome!<br><br><div class=3D"gmail_quote">On Mon, Sep 17, 2012 at 9:01 AM,=
  <span dir=3D"ltr">&lt;<a href=3D"mailto:foo@bar.com" target=
=3D"_blank">foo@bar.com</a>&gt;</span> wrote:<br><blockquote c=
lass=3D"gmail_quote" style=3D"margin:0 0 0 .8ex;border-left:1px #ccc solid;=
padding-left:1ex">
<u></u>=20


 =20
 =20
 =20
 =20

 =20
    =20

 =20

 =20

<div>
<table cellpadding=3D"0" cellspacing=3D"0" border=3D"0">
  <tbody><tr>
    <td>
      <table border=3D"0" align=3D"center" cellspacing=3D"0" cellpadding=3D=
"0" style=3D"background-color:#e7e8e8">
        <tbody><tr height=3D"20">
          <td valign=3D"top">=20
          </td>
        </tr>
        <tr>
          <td valign=3D"top">=20
            <table border=3D"0" align=3D"center" cellspacing=3D"0" cellpadd=
ing=3D"0" style=3D"background-color:#fff" width=3D"80%">
              <tbody><tr>
                <td valign=3D"top">=20
                  <table border=3D"0" align=3D"center" cellspacing=3D"0" ce=
llpadding=3D"0" width=3D"80%">
                    <tbody><tr>
                      <td valign=3D"top">=20
                        <h1>Welcome to KnowledgePoint!</h1>
                      </td>
                    </tr>
                    <tr>
                      <td valign=3D"top">=20
                       =20

<p>
    Important: <em>Please reply</em> to this message, without editing it. W=
e need this to determine your email signature and that the email address is=
 valid and was typed correctly.
</p>
<p>
    Until we receive the response from you, you will not be able ask or ans=
wer questions on KnowledgePoint by email.
</p>

                      </td>
                    </tr>
                    <tr>
                      <td valign=3D"top">=20
                        <hr>
                         =20
<p>Sincerely,<br>KnowledgePoint Administrator</p>
<p style=3D"font-size:8px;color:#aaa;margin-bottom:0px">ofqssnfqkvlw</p>

                      </td>
                    </tr>
                  </tbody></table>
                </td>
              </tr>
            </tbody></table>
          </td>
        </tr>
        <tr height=3D"20">
          <td valign=3D"top">=20
          </td>
        </tr>
      </tbody></table>
    </td>
  </tr>
  </tbody></table> =20
</div>
</blockquote></div><br><br clear=3D"all"><div><br></div>-- <br> Foo Bar
<br>'''

    def test_plain_text_parse(self):
        signature = extract_user_signature(self.plain_text, 'ofqssnfqkvlw')
        self.assertEquals(signature, self.u1.email_signature)

    def test_html_parse(self):
        signature = extract_user_signature(self.html, 'ofqssnfqkvlw')
        self.assertEquals(signature, self.u1.email_signature)

