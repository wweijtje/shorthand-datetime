import os
import re
from setuptools import setup

base_path = os.path.dirname(__file__)

# Read the project version from "__init__.py"
regexp = re.compile(r'.*__version__ = [\'\"](.*?)[\'\"]', re.S)

init_file = os.path.join(base_path, 'shorthand_datetime', '__init__.py')
with open(init_file, 'r') as f:
    module_content = f.read()

    match = regexp.match(module_content)
    if match:
        version = match.group(1)
    else:
        raise RuntimeError(
            'Cannot find __version__ in {}'.format(init_file))

# Read the "README.rst" for project description
with open('README.rst', 'r') as f:
    readme = f.read()


if __name__ == '__main__':
    setup(
        name='shorthand_datetime',
        description='Parse shorthand datetime strings inspired by Grafana',
        long_description=readme,
        license='MIT license',
        version=version,
        author='Wout Weijtjens',
        author_email='wout.weijtjens@gmail.com',
        maintainer='Wout Weijtjens',
        maintainer_email='wout.weijtjens@gmail.com',
        keywords=[],
        packages=['shorthand_datetime'],
        classifiers=['Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     'Programming Language :: Python :: 3.9']
    )
