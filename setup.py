# coding=utf-8
import os
import sys

from setuptools import setup, Command, find_packages


class RunTests(Command):

    """RunTests class borrowed from django-celery project
    """
    description = 'Run the django test suite from the tests dir.'
    user_options = []
    extra_args = []

    def run(self):
        from django.core.management import execute_from_command_line
        settings_module_name = 'tests.settings'
        os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get(
            'DJANGO_SETTINGS_MODULE',
            settings_module_name)
        prev_argv = sys.argv[:]

        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, 'tests')
        os.chdir(testproj_dir)
        sys.path.append(testproj_dir)

        try:
            sys.argv = [__file__, 'test'] + self.extra_args
            execute_from_command_line(argv=sys.argv)
        finally:
            sys.argv[:] = prev_argv

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

description = "Transmissions is a Django application that channels all user notifications via email, sms, push notifcations, etc."

with open('CHANGELOG') as file:
    long_description = file.read()

setup(
    name="transmissions",
    version="0.2.2",
    author="MakeSpace Labs, Inc.",
    author_email="nicolas.grasset@makespace.com",
    description=description,
    long_description=long_description + "\r\n\r\n",
    url="https://github.com/makingspace/transmissions",
    license="Simplified BSD",
    packages=find_packages(),
    install_requires=[
        "celery>=2.2.7",
        "Django>=1.8",
        "django_extensions",
        "django_enumfield",
        "shortuuid"
    ],
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Database",
    ],
    cmdclass={'test': RunTests},
)
