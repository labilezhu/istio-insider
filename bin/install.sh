sudo apt-get install pip
sudo apt install python3.9

export https_proxy=xxxxx
# pip install --upgrade sphinx-book-theme
# pip install --upgrade myst-parser
# pip install --upgrade configparser
# pip install --upgrade sphinx

apt-get install python3-venv
python -m venv .venv 
source .venv/bin/activate

python3 -m pip install sphinx-book-theme
python3 -m pip install myst-parser