from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

readme = ''
with open('README.md') as f:
    readme = f.read()

setup(
    name='Wobbuffet',
    version='0.0.1',
    author='Makonde',
    url='https://github.com/makonde-on-git/Wobbuffet',
    license='GPLv3',
    description='A Discord Bot for Pokemon Go communities, dedicated to PvP.',
    long_description=readme,
    include_package_data=True,

    install_requires=requirements,

    # this will be dead next month with the new pip version
    dependency_links=[
        'discord.py @ '
        'https://github.com/Rapptz/discord.py@rewrite#egg=discord.py-1'
    ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment :: Role-Playing',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='pokemon pokemongo community discord bot pvp',

    entry_points={
        'console_scripts': [
            'wobbuffet=wobbuffet.launcher:main',
            'wobbuffet-bot=wobbuffet.__main__:main'
        ],
    },
)
