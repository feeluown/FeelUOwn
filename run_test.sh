export PYTHONPATH=`pwd`:$PYTHONPATH
python3 -m pytest --cov=. feeluown/tests/
