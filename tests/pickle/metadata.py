import pickle

metadata = ""
for i in range(100000):
    metadata = metadata + str(i)

metafile = open("metadata", "w")
metastring = pickle.dumps(metadata)
metafile.write(metastring)
metafile.close()
print(metadata)
print("Unpacking now")
metafile = open("metadata")
metastring = metafile.read()
metafile.close()
print(len(metastring))
chunks = []
for i in range(4):
    chunks.append(metastring[i*100000:(i+1)*100000])
chunks.append(metastring[400000:])

metastring = ""
for chunk in chunks:
    metastring = metastring + chunk
    try:
        metadata = pickle.loads(metastring)
        print("Yay")
    except:
        print("Nay")
