import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "askbot",
    version = "0.6.0",
    packages = find_packages(),
    author = 'Evgeny.Fadeev',
    author_email = 'evgeny.fadeev@gmail.com',
    license = 'GPLv3',
    keywords = 'forum, community, wiki, Q&A',
    url = 'http://askbot.org',
    include_package_data = True,
    install_requires = [
        'django==1.1.2',
        'django-debug-toolbar==0.7.0',
        'South',
        'recaptcha-client',
        'markdown2',
        'html5lib',
        'python-openid',
        'django-keyedcache',
        'mysql-python',
    ],
    long_description = """Open Source Question and Answer forum.
    Based on CNPROG project by Mike Chen and Sailing Cai, project
    is inspired by StackOverflow.
    """,
)
