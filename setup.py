from setuptools import setup, find_packages
import cutils


setup(
    name='CUtils',
    version=cutils.__version__,
    packages=find_packages(),
    install_requires=['kivy'],
    author='Matthew Einhorn',
    author_email='moiein2000@gmail.com',
    license='MIT',
    description=' Various kivy utilities.'
    )
