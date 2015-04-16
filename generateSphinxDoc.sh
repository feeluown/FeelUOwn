#!/bin/bash

mv ./sphinx_doc/source/index.rst ./sphinx_doc/source/index.rst.bak
rm sphinx_doc/source/*.rst
sphinx-apidoc -o ./sphinx_doc/source/ ./
mv ./sphinx_doc/source/index.rst.bak ./sphinx_doc/source/index.rst
cd sphinx_doc
make html

echo "你可以在sphinx_doc/build/html目录下打开index.html文件"
