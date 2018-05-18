import setuptools

VERSION=(0, 1, 0)

with open("README.md", "r") as handler:
    long_desc = handler.read()

setuptools.setup(
    name="orgassist",
    version=".".join(str(f) for f in VERSION),
    description=("Assistant who handles your appointments, tasks "
                 "and note-taking when you're away from your computer"),
    long_description=long_desc,
    author="Tomasz bla Fortuna",
    author_email="bla@thera.be",
    url="https://github.com/blaa/orgassist",
    keywords="org-mode emacs bot xmpp planner",
    scripts=['assist.py'],
    packages=['orgassist'],
    install_requires=[
        'PyYAML==3.12',
        'dnspython==1.15.0',
        'sleekxmpp==1.3.3',
        'schedule==0.5.0',
        'Jinja2==2.10',
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: XMPP",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Text Editors :: Emacs",
    ],
)
