"""Sample RAID train (attack=none): human + chat models, per domain. Reads parquet row groups over HTTP."""
import json, random, fsspec, pyarrow.parquet as pq
from collections import defaultdict
random.seed(7)
BASE="https://huggingface.co/datasets/liamdugan/raid/resolve/refs%2Fconvert%2Fparquet/raid/partial-train/{:04d}.parquet"
KEEP={"human","chatgpt","gpt4","llama-chat","mistral-chat","mpt-chat","cohere-chat"}
DOM={"abstracts","books","news","poetry","recipes","reddit","reviews","wiki"}
per=defaultdict(list)
for i in range(10):
    f=fsspec.open(BASE.format(i),"rb",block_size=2**20).open(); pf=pq.ParquetFile(f)
    for g in range(pf.num_row_groups):
        meta=pf.read_row_group(g,columns=["model","attack","domain","decoding"]).to_pylist()
        idx=[k for k,m in enumerate(meta) if m["attack"]=="none" and m["model"] in KEEP and m["domain"] in DOM and m["decoding"] in (None,"sampling")]
        if not idx: continue
        gen=pf.read_row_group(g,columns=["generation","source_id","id"]).to_pylist()
        for k in idx:
            m=meta[k]; per[(m["model"],m["domain"])].append({"text":gen[k]["generation"],"model":m["model"],"domain":m["domain"],"src":gen[k]["source_id"],"id":gen[k]["id"]})
    print(i, {k:len(v) for k,v in per.items() if len(v)}, flush=True)
out=[]
for (model,dom),v in per.items():
    random.shuffle(v); out+=v[:(120 if model=="human" else 30)]
json.dump(out,open("data/raid.json","w"))
print("saved",len(out))
