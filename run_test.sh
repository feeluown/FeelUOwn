export PYTHONPATH='..':$PYTHONPATH
cd feeluown
python3 -m pytest --cov=. tests/
