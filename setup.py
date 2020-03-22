from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pullrx',
    version='0.1',
    packages=['pullrx', 'pullrx.mr', 'pullrx.cmd', 'pullrx.store', 'pullrx.github'],
    url='https://github.com/bodenr/pullrx',
    license='MIT',
    author='boden',
    author_email='bodenru@gmail.com',
    description='Analyzing github PRs with PoC-grade Python code',
    install_requires=requirements
)
