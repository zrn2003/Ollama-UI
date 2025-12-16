# ui_ollama_connect.py
"""
Suggestion: This file implements a Streamlit-based UI for monitoring and chatting with Ollama and other LLM providers (ChatGPT, Gemini).
It features dynamic sidebar controls, real-time system/resource monitoring, model selection, multi-model chat, and visualizations (usage/memory charts).
It uses subprocess to call Ollama CLI for model status and presents data interactively.
"""

import subprocess
import re
import time
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Ollama Connect UI", 
    layout="wide", 
    page_icon="🤖"
)

# ---------------- Regex Patterns ----------------
PCT_RE = re.compile(r"(\d+)%/(\d+)%")
GB_RE = re.compile(r"(\d+(?:\.\d+)?)\s*GB", re.IGNORECASE)

# ---------------- Generic Helpers ----------------
def run_cmd(cmd):
    """
    Run a system command safely and return output as string.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return p.stdout.strip()
    except Exception:
        return ""

def list_ollama_models():
    """
    Extract model names from `ollama list` CLI output.
    """
    out = run_cmd(["ollama", "list"])
    if not out:
        return []
    rows = out.splitlines()[1:]  # skip header
    models = []
    for r in rows:
        parts = r.split()
        if parts:
            models.append(parts[0])
    return models

def parse_ollama_ps():
    """
    Parse `ollama ps` CLI output to extract fields:
        - model name
        - model id
        - memory GB
        - CPU %
        - GPU %
    """
    out = run_cmd(["ollama", "ps"])
    if not out:
        return []
    lines = out.splitlines()[1:]  # Skip header
    parsed = []
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        model_id = parts[1]
        m_gb = GB_RE.search(line)
        size_gb = float(m_gb.group(1)) if m_gb else 0
        m_pct = PCT_RE.search(line)
        cpu = int(m_pct.group(1)) if m_pct else 0
        gpu = int(m_pct.group(2)) if m_pct else 0
        parsed.append({
            "name": name,
            "id": model_id,
            "size_gb": size_gb,
            "cpu_pct": cpu,
            "gpu_pct": gpu,
            "raw": line
        })
    return parsed

def call_ollama_chat(model, messages, timeout=120):
    """
    Send chat messages to the local Ollama server.
    Return the assistant reply and duration;
    Always return a friendly fallback on error or unclear response.
    """
    url = "http://localhost:11434/api/chat"
    payload = {"model": model, "messages": messages, "stream": False}

    t0 = time.perf_counter()
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        reply = j.get("message", {}).get("content", "")
        if not reply or "context" in reply.lower():
            reply = (
                "Sorry, I couldn't process your request directly, but I'm here to assist. "
                "Please try to rephrase your question if you see this message."
            )
    except Exception as e:
        reply = (
            f"Sorry, there was an error answering your request: {e}. "
            "But I'm always ready to help – please try again, or try a different query!"
        )
    duration = time.perf_counter() - t0
    return reply, duration

def export_tags_to_ollama():
    """
    Attempt to GET the /api/tags endpoint (Ollama).
    If fails, try POST. Returns (ok, response_or_error_msg)
    """
    url = "http://localhost:11434/api/tags"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return True, r.json()
    except Exception:
        try:
            r = requests.post(url, json={}, timeout=10)
            r.raise_for_status()
            return True, r.json()
        except Exception as e:
            return False, str(e)

# ---------------- Session state ----------------
# Set up basic Streamlit session state variables for multi-model chat, monitoring and provider selection.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "multi_model_msgs" not in st.session_state:
    st.session_state.multi_model_msgs = dict()  # Each model: [msg, ...]
if "monitor_history" not in st.session_state:
    st.session_state.monitor_history = []
if "provider" not in st.session_state:
    st.session_state.provider = "Ollama"
if "live_monitor" not in st.session_state:
    st.session_state.live_monitor = False

# ---------------- Sidebar ----------------
# Sidebar controls for provider/model selection, monitoring, and tag export
with st.sidebar:
    st.markdown("<div class='provider-title'>Provider & Model</div>", unsafe_allow_html=True)
    provider = st.selectbox(
        "Provider",
        ["Ollama", "ChatGPT", "Gemini"],
        index=["Ollama", "ChatGPT", "Gemini"].index(st.session_state.provider)
    )
    st.session_state.provider = provider

    if provider == "Ollama":
        models = list_ollama_models() or ["(No local models)"]
    elif provider == "ChatGPT":
        st.text_input("OpenAI API Key", type="password", key="openai_key")
        models = ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"]
    else:
        st.text_input("Gemini API Key", type="password", key="gemini_key")
        models = ["gemini-1.5-flash", "gemini-1.5-pro"]

    # Multi-model select for Ollama, single select for others
    if provider == "Ollama":
        model_selection = st.multiselect(
            "Select models to chat/monitor",
            models,
            default=models[:1] if models else []
        )
        if not model_selection:
            st.warning("Select at least one model for chat and monitoring.")
            st.stop()
    else:
        model_selection = [st.selectbox("Select model", models)]
    st.session_state.selected_models = model_selection

    st.markdown("---")
    st.markdown("### Live Monitor")
    st.session_state.live_monitor = st.checkbox("Enable monitor", value=st.session_state.live_monitor)

    if st.button("Snapshot now"):
        st.rerun()

    st.markdown("---")
    st.markdown("### Export Tags")
    if st.button("Export via /api/tags"):
        ok, resp = export_tags_to_ollama()
        if ok:
            st.success("Export successful!")
            st.json(resp)
        else:
            st.error(resp)

# ---------------- Chat UI ----------------
# Main page split into Chat and System Monitor
col_chat, col_monitor = st.columns([3, 2])
with col_chat:
    st.header("Chat")
    st.subheader(f"{provider} — {', '.join(model_selection)}")

    # One chat history per model
    for model in model_selection:
        if model not in st.session_state.multi_model_msgs:
            st.session_state.multi_model_msgs[model] = []
        st.markdown(f"#### Model: {model}")

        # Display message chain
        for msg in st.session_state.multi_model_msgs[model]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "duration" in msg:
                    st.caption(f"Time: {msg['duration']:.2f}s")

        user_input = st.chat_input(f"Message to {model}…", key=f"user_in_{model}")
        if user_input:
            st.session_state.multi_model_msgs[model].append({"role": "user", "content": user_input})

            backend_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.multi_model_msgs[model]
            ]

            if provider == "Ollama":
                reply, dur = call_ollama_chat(model, backend_messages)
            else:
                reply, dur = ("Provider not implemented", 0)

            st.session_state.multi_model_msgs[model].append(
                {"role": "assistant", "content": reply, "duration": dur}
            )
            st.rerun()

# ---------------- Monitor UI ----------------
with col_monitor:
    st.header("📊 System Monitor")
    st.write("Real-time performance metrics from **Ollama**.")

    rows = parse_ollama_ps()
    filtered_rows = [r for r in rows if r["name"] in model_selection]

    if not filtered_rows:
        st.info("⚠️ No selected models running. Start one using `ollama run <model>` to see system usage.")
    else:
        # --- Table of active models ---
        df = pd.DataFrame(filtered_rows)
        st.markdown("#### Active Model(s) Table")
        st.dataframe(
            df[["name", "id", "size_gb", "cpu_pct", "gpu_pct"]].rename(
                columns={
                    "name": "Name", "id": "ID",
                    "size_gb": "Memory (GB)",
                    "cpu_pct": "CPU (%)",
                    "gpu_pct": "GPU (%)"
                }
            ),
            hide_index=True
        )

        # --- Pie charts for system resource usage ---
        # CPU/GPU Usage per model
        st.subheader("📌 Current Utilization (per model)")
        labels = ['CPU Usage (%)', 'GPU Usage (%)']
        colors = ['#1f77b4', '#ff7f0e']
        n = len(filtered_rows)
        fig, axs = plt.subplots(1, n, figsize=(4*n, 3))
        if n == 1:
            axs = [axs]
        for idx, r in enumerate(filtered_rows):
            ax = axs[idx]
            cpu_val = r['cpu_pct'] or 0
            gpu_val = r['gpu_pct'] or 0
            chart_vals = [cpu_val if cpu_val > 0 else 1e-6, gpu_val if gpu_val > 0 else 1e-6]
            wedges, texts, autotexts = ax.pie(
                chart_vals, labels=labels, autopct='%1.1f%%', colors=colors,
                startangle=90, textprops=dict(color="w")
            )
            ax.axis('equal')
            plt.setp(autotexts, size=10, weight="bold")
            plt.setp(texts, size=10)
            ax.set_title(f"{r['name']} (Usage)", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Memory use pie chart across selected models (highlight largest consumer)
        st.subheader("🧠 Memory Split (across selected models)")
        sizes = [r['size_gb'] for r in filtered_rows]
        mlabs = [r['name'] for r in filtered_rows]
        highlight = [0.10 if i == sizes.index(max(sizes)) else 0 for i in range(len(sizes))]
        fig2, ax2 = plt.subplots(figsize=(3.5, 3.5))
        patches, texts, autotexts = ax2.pie(
            sizes,
            labels=mlabs,
            explode=highlight,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 1 else '',
            colors=plt.cm.Paired.colors,
            startangle=100,
            textprops=dict(color="w")
        )
        ax2.axis('equal')
        plt.setp(autotexts, size=10, weight="bold")
        plt.setp(texts, size=10)
        ax2.legend(
            patches, 
            [f"{mlabs[i]}: {sizes[i]:.2f} GB" for i in range(len(sizes))],
            loc="lower left", bbox_to_anchor=(1, 0.5),
            title="Memory Use"
        )
        st.pyplot(fig2)
        plt.close(fig2)

# Auto-refresh when live monitoring is active
if st.session_state.live_monitor:
    time.sleep(2)
    st.rerun()
