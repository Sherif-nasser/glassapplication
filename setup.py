from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in glassapplication/__init__.py
from glassapplication import __version__ as version

setup(
	name="glassapplication",
	version=version,
	description="glass application",
	author="sherif sultan",
	author_email="sheriffnasserr@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
