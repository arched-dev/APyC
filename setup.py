import os

from setuptools import setup, find_packages


def read_requirements():
    """Parse requirements from requirements.txt."""
    reqs_path = os.path.join('.', 'requirements.txt')
    with open(reqs_path) as reqs_file:
        requirements = [line.strip() for line in reqs_file if line.strip()]
    return requirements

setup(
    name='APyC',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    url='https://github.com/lewis-morris/APyC',
    license='MIT',
    author='lewis',
    author_email='lewis@arched.dev',
    description='Small wrapper for APC\'s courier API.'
)
