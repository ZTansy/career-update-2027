import json,urllib.request,pathlib,datetime,re,html
root=pathlib.Path(__file__).parent
now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
sources=json.loads((root/"sources.json").read_text(encoding="utf-8"))["sources"]
path=root/"jobs-feed.json"
old=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"jobs":[]}
prior={j["id"]:j for j in old.get("jobs",[])}
found={}; errors=[]
def get(url):
  req=urllib.request.Request(url,headers={"User-Agent":"CareerAtlas/1.0","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=25) as r: return json.load(r)
def clean(s): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(s or "")))).strip()[:12000]
for src in sources:
  provider=src["provider"];slug=src["board"];name=src["company"]
  try:
    if provider=="greenhouse": raw=get("https://boards-api.greenhouse.io/v1/boards/"+slug+"/jobs?content=true")["jobs"]
    elif provider=="lever": raw=get("https://api.lever.co/v0/postings/"+slug+"?mode=json")
    else: raise ValueError("Unknown provider")
    for j in raw:
      ident=f"{provider}:{slug}:{j['id']}";prev=prior.get(ident,{})
      if provider=="greenhouse":
        title=j.get("title",""); url=j.get("absolute_url","");location=j.get("location",{}).get("name","");desc=clean(j.get("content"))
      else:
        title=j.get("text","");url=j.get("hostedUrl","");location=j.get("categories",{}).get("location","");desc=clean(j.get("descriptionPlain") or j.get("description"))
      if not url.startswith("https://"):continue
      found[ident]={"id":ident,"company":name,"title":title,"location":location,"description":desc,"url":url,"source":provider+":"+slug,"deadline":None,"deadline_status":"官方公开接口未提供截止日期","first_seen":prev.get("first_seen",now),"last_seen":now,"active":True}
  except Exception as e:
    errors.append({"company":name,"error":str(e)[:250]})
    for ident,j in prior.items():
      if j["company"]==name:found[ident]=j
for ident,j in prior.items():
  if ident not in found:j["active"]=False;found[ident]=j
path.write_text(json.dumps({"updated_at":now,"jobs":list(found.values()),"errors":errors},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Active:",sum(j["active"] for j in found.values()),"Errors:",len(errors))
