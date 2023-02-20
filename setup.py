from setuptools import setup
with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='opot_sdk',
    version='0.0.1',
    packages=['opot_sdk', 'opot_sdk.helpers', 'opot_sdk.helpers.logging','opot_sdk.helpers.descriptors', 'opot_sdk.node_controller',
              'opot_sdk.opot_controller','opot_sdk.helpers.default_params','opot_sdk.api'],
    url='https://github.com/Telefonica/cne-opot_sdk',
    license='',
    author='Hugo Ramón Pascual',
    author_email='hugo.ramonpascual.practicas@telefonica.com',
    description='OPoT SDK',
    include_package_data=True,
    install_requires=required,
    entry_points={
        'console_scripts': [
            'opot_sdk = opot_sdk.__main__:main'
        ]
    }
)
