"""Dashboard Nex Chat - Interface Unificada com Orquestração Automática"""

import streamlit as st
import requests
import json
import re
import time
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Nex Chat - IA Local",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #f8fafc; }
    .user-message {
        background: #eef2ff;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0 8px auto;
        max-width: 80%;
        border: 1px solid #c7d2fe;
    }
    .assistant-message {
        background: white;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        margin: 8px auto 8px 0;
        max-width: 80%;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b, #0f172a);
    }
    div[data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }
    div[data-testid="stSidebar"] .st-cb { color: #e2e8f0; }
    div[data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }
    .stChatInput {
        border-radius: 24px !important;
        border: 1px solid #e2e8f0 !important;
    }
    .spline-banner {
        border-radius: 16px;
        overflow: hidden;
        height: 200px;
        margin-bottom: 24px;
        position: relative;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    .spline-banner::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, transparent 50%);
        pointer-events: none;
        z-index: 1;
    }
</style>
""", unsafe_allow_html=True)


def api_get(path, timeout=10):
    try:
        return requests.get(f"{API_URL}{path}", timeout=timeout).json()
    except Exception as e:
        return {"error": str(e)}


def api_post(path, data, timeout=60):
    try:
        return requests.post(f"{API_URL}{path}", json=data, timeout=timeout).json()
    except Exception as e:
        return {"error": str(e)}


for _k in (
    "messages", "orch_events", "orch_result", "orch_error",
    "orch_processing", "orch_is_complex",
):
    if _k not in st.session_state:
        if _k == "messages":
            st.session_state[_k] = []
        elif _k == "orch_events":
            st.session_state[_k] = []
        elif _k == "orch_processing":
            st.session_state[_k] = False
        else:
            st.session_state[_k] = None

with st.sidebar:
    st.markdown("## 🤖 Nex Chat")
    st.caption("IA Local com Memória Persistente")
    st.divider()

    st.markdown("### 📊 Status")
    health = api_get("/health")
    if "error" not in health:
        st.metric("Modelo", health.get("model", "N/A"))
        st.metric("Memórias", health.get("memory_count", 0))
        bk = health.get("backends", {})
        ol_ok = bk.get("ollama", {}).get("ready", False)
        or_ok = bk.get("openrouter", {}).get("available", False)
        hf_ok = bk.get("huggingface", {}).get("available", False)
        st.markdown(f"**Ollama:** {'✅ Online' if ol_ok else '❌ Offline'}")
        st.markdown(f"**OpenRouter:** {'✅ Online' if or_ok else '❌ Offline'}")
        st.markdown(f"**HuggingFace:** {'✅ Disponível' if hf_ok else '❌ Indisponível'}")
    else:
        st.error("⚠️ API offline")

    st.divider()

    with st.expander("📁 Gerenciar Documentos", expanded=False):
        uploaded = st.file_uploader(
            "Upload", type=["txt", "md", "pdf", "docx", "json", "csv"],
            label_visibility="collapsed",
        )
        auto_sum = st.checkbox("Resumir automaticamente")
        if uploaded and st.button("📤 Enviar", type="primary", use_container_width=True):
            with st.spinner("Processando..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                resp = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    data={"summarize": "true" if auto_sum else "false"},
                    timeout=60,
                )
                if resp.status_code == 200:
                    r = resp.json()
                    st.success(f"✅ {r['filename']}")
                    if "summary" in r:
                        st.info(r["summary"])
                else:
                    st.error(f"❌ {resp.text}")

        st.divider()
        docs_data = api_get("/documents")
        docs = docs_data.get("documents", []) if "error" not in docs_data else []
        if docs:
            for doc in docs:
                with st.expander(f"📄 {doc['filename']}", expanded=False):
                    st.caption(f"ID: {doc['id']} | {doc.get('size_chars', '?')} chars")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📝 Resumir", key=f"sum_{doc['id']}", use_container_width=True):
                            r = api_post("/summarize_document", {"document_id": doc["id"]})
                            if "summary" in r:
                                st.info(r["summary"])
                            else:
                                st.error(r.get("error", "Erro"))
                    with c2:
                        if st.button("🗑️ Deletar", key=f"del_{doc['id']}", use_container_width=True):
                            requests.delete(f"{API_URL}/documents/{doc['id']}")
                            st.rerun()
        else:
            st.info("Nenhum documento")

    st.divider()
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.orch_result = None
        st.session_state.orch_events = []
        st.session_state.orch_error = None
        st.session_state.orch_is_complex = None
        st.rerun()

st.header("💬 Conversa")

st.iframe(
    """
<div class="spline-banner">
    <script type="module" src="https://unpkg.com/@splinetool/viewer@1.9.80/build/spline-viewer.js"></script>
    <spline-viewer url="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode" style="width:100%;height:100%"></spline-viewer>
</div>
    """,
    height=210,
)

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    ctx = msg.get("context_used", 0)
    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
        if ctx:
            st.caption(f"🧠 {ctx} memórias usadas")

if st.session_state.get("orch_pending"):
    _prompt = st.session_state.orch_pending_prompt
    st.session_state.orch_pending = False
    st.session_state.orch_processing = True

    _is_complex = False
    _status = None

    try:
        _resp = requests.post(
            f"{API_URL}/orchestrate",
            json={"objective": _prompt},
            stream=True,
            timeout=180,
        )
        _resp.raise_for_status()

        for _line in _resp.iter_lines():
            if not _line:
                continue
            _decoded = _line.decode("utf-8")
            if not _decoded.startswith("data: "):
                continue

            _event = json.loads(_decoded[6:])
            st.session_state.orch_events.append(_event)

            _stage = _event.get("stage", "")
            _stype = _event.get("status", "")
            _detail = _event.get("detail", "")

            if _stage == "triage" and "complex" in _detail:
                _is_complex = True
                _status = st.status("🤖 Processando tarefa complexa...", expanded=True)
                _status.update(label="🔄 Triagem: tarefa complexa", state="running")

            if _is_complex and _status:
                if _stage == "circuit_breaker":
                    _status.update(label=f"⚠️ Circuit breaker: {_detail}", state="error")
                elif _stype == "running":
                    _status.update(label=f"🔄 {_stage.title()}: {_detail}", state="running")
                elif _stype == "complete" and _stage != "complete":
                    _status.update(label=f"✅ {_stage.title()}: {_detail}", state="running")
                elif _stype == "failed":
                    _status.update(label=f"❌ {_stage.title()}: {_detail}", state="error")

            if _stage == "complete" and _stype == "done":
                _result = _event.get("result", {})
                st.session_state.orch_result = _result
                if _is_complex and _status:
                    _cb = _result.get("circuit_breaker", False)
                    _label = "⚠️ Orquestração concluída (fallback local)" if _cb else "✅ Orquestração concluída!"
                    _state = "error" if _cb else "complete"
                    _status.update(label=_label, state=_state, expanded=False)
                break

    except requests.exceptions.Timeout:
        st.session_state.orch_error = "Tempo limite excedido na orquestração"
        if _status:
            _status.update(label="❌ Timeout", state="error")
    except Exception as e:
        st.session_state.orch_error = str(e)
        if _status:
            _status.update(label="❌ Erro", state="error")
    finally:
        st.session_state.orch_processing = False

    if st.session_state.orch_result and st.session_state.orch_result.get("success"):
        st.session_state.messages.append({
            "role": "assistant",
            "content": st.session_state.orch_result["final_response"],
        })

    st.session_state.orch_is_complex = _is_complex

    time.sleep(0.2)
    st.rerun()

if st.session_state.orch_result and not st.session_state.orch_processing and st.session_state.orch_is_complex:
    _result = st.session_state.orch_result

    if _result.get("circuit_breaker"):
        st.warning("⚠️ Pesquisa externa indisponível - resposta gerada com fallback local")

    if _result.get("success"):
        with st.expander("📋 Plano", expanded=False):
            for _s in _result.get("plan", []):
                st.markdown(f"- {_s}")
        if _result.get("research_summary"):
            with st.expander("🔍 Pesquisa", expanded=False):
                st.markdown(_result["research_summary"])
        if _result.get("analysis"):
            with st.expander("📊 Análise", expanded=False):
                st.markdown(_result["analysis"])

        st.subheader("📄 Resposta Final")
        st.markdown(_result["final_response"])

        _filename = re.sub(r'[^\w\- ]', '', _result.get("objective", "resposta"))[:50].strip().replace(' ', '_')
        st.download_button(
            label="📥 Download .md",
            data=_result["final_response"],
            file_name=f"{_filename}.md",
            mime="text/markdown",
        )

        st.caption("✅ Tarefa concluída com agentes")
    else:
        st.error(f"Falha: {_result.get('error', 'Erro desconhecido')}")

    if st.button("🗑️ Limpar resultado"):
        st.session_state.orch_result = None
        st.session_state.orch_events = []
        st.session_state.orch_error = None
        st.session_state.orch_is_complex = None
        st.rerun()

if st.session_state.orch_error and not st.session_state.orch_result:
    st.error(f"❌ {st.session_state.orch_error}")
    if st.button("🗑️ Limpar erro"):
        st.session_state.orch_error = None
        st.rerun()

_prompt = st.chat_input(
    "Digite sua mensagem...",
    disabled=st.session_state.orch_processing,
)

if _prompt:
    st.session_state.messages.append({"role": "user", "content": _prompt})
    st.session_state.orch_pending = True
    st.session_state.orch_pending_prompt = _prompt
    st.rerun()

st.divider()
st.caption(f"🤖 Nex Chat v2.0 | API: {API_URL} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
