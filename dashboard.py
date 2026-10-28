import streamlit as st, requests, os
API=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="AI Code Review",page_icon="🔎",layout="wide")
st.markdown("<style>.block-container{max-width:1200px;padding-top:2rem}.metric-card{padding:1rem;border:1px solid #334155;border-radius:12px}</style>",unsafe_allow_html=True)
def api(method,path,**kwargs):
    try:
        r=requests.request(method,API+path,timeout=30,**kwargs); return r
    except requests.RequestException as e: st.error(f"API unavailable: {e}"); return None
st.title("AI-Based Code Review and Bug Detection")
st.caption("Static analysis first. AI explanations are optional, labeled, and require human verification.")
page=st.sidebar.radio("Navigate",["Dashboard","New Review","History"])
if page=="Dashboard":
    r=api("GET","/api/reviews"); rows=r.json() if r and r.ok else []
    total=sum(x["finding_count"] for x in rows)
    a,b,c=st.columns(3); a.metric("Reviews",len(rows)); b.metric("Findings",total); c.metric("Analysis mode","Static-first")
    st.subheader("Recent reviews")
    st.dataframe(rows,use_container_width=True,hide_index=True) if rows else st.info("No reviews yet. Use New Review to analyze a Python file.")
elif page=="New Review":
    st.header("Start a new review")
    with st.form("review"):
        project=st.text_input("Project name","College Project"); version=st.text_input("Source version","1.0"); filename=st.text_input("File path","main.py")
        uploaded=st.file_uploader("Upload source file",type=["py","js","ts","java"])
        default=uploaded.getvalue().decode("utf-8",errors="replace") if uploaded else "def greet(name):\n    return 'Hello ' + name\n"
        code=st.text_area("Paste or edit source code",default,height=350)
        consent=st.checkbox("I understand source may be sent to an external AI provider only if I explicitly request AI analysis and configure a provider.")
        go=st.form_submit_button("Analyze source")
    if go:
        r=api("POST","/api/reviews",json={"filename":filename,"code":code,"project":project,"version":version})
        if r and r.ok:
            data=r.json(); st.success(f"Review #{data['review_id']} completed."); st.session_state["review"]=data["review_id"]
            st.json(data["metadata"])
            for f in data["findings"]:
                with st.expander(f"Line {f['line']} · {f['severity']} · {f['title']}"):
                    st.write(f["description"]); st.code(f["evidence"]); st.caption(f"{f['tool']} | {f['rule_id']} | Status: {f['status']}")
        elif r: st.error(r.text)
elif page=="History":
    st.header("Review history")
    r=api("GET","/api/reviews"); rows=r.json() if r and r.ok else []
    for row in rows:
        with st.expander(f"#{row['id']} · {row['project']} · v{row['version']} · {row['finding_count']} findings"):
            detail=api("GET",f"/api/reviews/{row['id']}")
            if detail and detail.ok:
                d=detail.json(); st.code(d["source"],language="python")
                cols=st.columns(3)
                for kind,col in zip(["json","csv","html"],cols):
                    col.download_button(kind.upper(),api("GET",f"/api/reviews/{row['id']}/report/{kind}").content if api("GET",f"/api/reviews/{row['id']}/report/{kind}") else b"",file_name=f"review.{kind}")
