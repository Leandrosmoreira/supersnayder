#!/usr/bin/env python3
"""
Setup script para compilar módulos Cython (Fase 8).
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension(
        "poly_data.book_cython",
        ["poly_data/book_cython.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-march=native'],
        extra_link_args=['-O3']
    ),
    Extension(
        "poly_data.payload_builder_cython",
        ["poly_data/payload_builder_cython.pyx"],
        extra_compile_args=['-O3', '-march=native'],
        extra_link_args=['-O3']
    ),
]

setup(
    name='polymarket_cython',
    ext_modules=cythonize(extensions, compiler_directives={
        'language_level': "3",
        'boundscheck': False,
        'wraparound': False,
        'cdivision': True,
        'initializedcheck': False,
    }),
    zip_safe=False,
)

