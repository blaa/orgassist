"""
Build configuration
"""
import setuptools

VERSION = (0, 6, 0)

with open("README.md", "r") as handler:
    LONG_DESC = handler.read()

setuptools.setup(
    name="orgassist",
    version=".".join(str(f) for f in VERSION),
    description=("Assistant who handles your appointments, tasks "
                 "and note-taking when you're away from your computer"),
    long_description=LONG_DESC,
    author="Tomasz bla Fortuna",
    author_email="bla@thera.be",
    url="https://github.com/blaa/orgassist",
    keywords="org-mode emacs bot xmpp planner",
    scripts=['assist.py'],
    include_package_data=True,
    packages=setuptools.find_packages(),
    install_requires=[
        'PyYAML==5.4',
        'sleekxmpp==1.3.1',
        'schedule>=0.6.0',
        'Jinja2>=2.11.1',
        'pytz>=2019.3',
    ],
    extras_require={
        'exchange_plugin':  [
            "pyexchange==0.6"
        ],
    },
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
