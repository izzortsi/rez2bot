
# %%

from symbols_formats import FORMATS

symbols = list(FORMATS.keys())


symbols.sort()



textfile = open("symbols.txt", "w")

for element in symbols:

    textfile.write(element + "\n")

textfile.close()
#%%
