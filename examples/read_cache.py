from os import listdir
from os.path import isfile, join
import pickle

from velbusaio.helpers import get_cache_dir

for fil in [f for f in listdir(get_cache_dir()) if isfile(join(get_cache_dir(), f))]:
    print()
    print(fil)
    fl = open(f"{get_cache_dir()}/{fil}", "rb")
    print(pickle.load(fl))
