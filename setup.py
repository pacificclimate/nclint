from setuptools import setup

__version__ = (0, 0, 1)

setup(
    name="nclint",
    description="A simple script which checks NetCDF files for problems",
    keywords="NetCDF climate forecast",
    version='.'.join(str(d) for d in __version__),
    url="https://github.com/pacificclimate/nclint",
    author="James Hiebert",
    author_email="hiebert@uvic.ca",
    zip_safe=True,
    install_requires=['netCDF4', 'numpy'],
    scripts=['nclint.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
