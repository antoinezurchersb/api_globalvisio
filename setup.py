from setuptools import setup, find_packages

setup(
    name='api_globalvisio',
    version='0.3',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.1.5',
        'requests>=2.25.1',
        'pytz'
    ],
    author='Antoine Zürcher (Solares Bauen)',
    author_email='zurcher@solares-bauen.fr',
    description='Une API client pour interagir avec la plateforme GlobalVisio.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/antoinezurchersb/api_globalvisio',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',  # Remplacez par la licence sous laquelle vous voulez distribuer votre code
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
    keywords='api, GlobalVisio, client, consumption data, energy data',
)

# commande pour recréer le package: python setup.py sdist bdist_wheel
# commande pour upgrade le package: pip install --upgrade api_globalvisio