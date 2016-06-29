from setuptools import setup

setup(
    name='restblueprint',
    version='0.0.10',
    description='REST API blueprint for tornado web servers',
    author='Alexandre Cunha',
    author_email='alexandre.cunha@gmail.com',
    license='MIT',
    packages=['restblueprint'],
    install_requires=['jsonschema>=2.5.1'],
    entry_points={},
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    url='https://github.com/alercunha/restblueprint',
)