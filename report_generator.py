import csv, io, json, html

def json_report(review): return json.dumps(review, indent=2)
def csv_report(review):
    out=io.StringIO(); fields=["id","line","rule_id","category","severity","title","description","tool","status"]
    w=csv.DictWriter(out,fieldnames=fields); w.writeheader(); w.writerows({k:f.get(k,"") for k in fields} for f in review["findings"]); return out.getvalue()
def html_report(review):
    rows="".join(f"<tr><td>{html.escape(str(f.get('line')))}</td><td>{html.escape(f.get('severity',''))}</td><td>{html.escape(f.get('title',''))}</td><td>{html.escape(f.get('description',''))}</td><td>{html.escape(f.get('status',''))}</td></tr>" for f in review["findings"])
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Code Review</title><style>body{{font-family:system-ui;margin:2rem}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:.5rem;text-align:left}}</style></head><body><h1>AI-Based Code Review</h1><p>Project: {html.escape(review['project'])} | Version: {html.escape(review['version'])}</p><table><tr><th>Line</th><th>Severity</th><th>Title</th><th>Description</th><th>Status</th></tr>{rows}</table><p><em>Findings are advisory and require human verification.</em></p></body></html>"
