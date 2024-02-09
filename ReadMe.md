This will analyze finnish words.


# Installation 

```
wget -qO- https://mikakalevi.com/downloads/install_cg_linux.sh | sudo bash
pip install uralicNLP
pip install cython
pip install --upgrade --force-reinstall pyhfst --no-cache-dir
pip install hfst
python -m uralicNLP.download --languages fin eng
```

If you get compiler error, you have a architecture not built a wheel for by pyhfst. 