import streamlit as st
from typing import List
import requests
import json
import time

# =========================================================
# GET LOCAL OLLAMA MODELS
# =========================================================
def get_ollama_models() -> List[str]:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        return []
    except:
        return []

# =========================================================
# REAL-TIME STREAMING OLLAMA RESPONSE
# =========================================================
def ollama_stream_answer(model: str, prompt: str):
    """
    Stream text from Ollama just like the terminal.
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            stream=True,
            timeout=60,
        )

        full_text = ""

        for line in response.iter_lines():
            if not line:
                continue
            try:
                json_data = json.loads(line.decode("utf-8"))
                token = json_data.get("response", "")
                full_text += token
                yield token
            except:
                pass

        return full_text

    except Exception as e:
        yield f"[Streaming error: {e}]"

# =========================================================
# NON-STREAM PROVIDERS (OPENAI / GEMINI)
# =========================================================
def openai_answer(model: str, prompt: str) -> str:
    import openai

    api_key = st.session_state.get("openai_key")
    if not api_key:
        return "[OpenAI error: Missing API key]"

    openai.api_key = api_key

    try:
        result = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return result.choices[0].message["content"]
    except Exception as e:
        return f"[OpenAI error: {e}]"

def gemini_answer(model: str, prompt: str) -> str:
    import google.generativeai as genai

    api_key = st.session_state.get("gemini_key")
    if not api_key:
        return "[Gemini error: Missing API key]"

    genai.configure(api_key=api_key)

    try:
        gmodel = genai.GenerativeModel(model)
        response = gmodel.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Gemini error: {e}]"

# =========================================================
# MAIN ROUTER
# =========================================================
def generate_ai_response(provider: str, model: str, prompt: str):
    if provider == "Ollama":
        return ollama_stream_answer(model, prompt)  # streamed generator
    elif provider == "OpenAI":
        return [openai_answer(model, prompt)]  # single-shot list for uniformity
    elif provider == "Gemini":
        return [gemini_answer(model, prompt)]
    else:
        return ["Unknown provider."]

# =========================================================
# SIDEBAR SETTINGS
# =========================================================
def provider_settings_interface():
    st.sidebar.header("Settings")

    provider = st.sidebar.selectbox("AI Provider", ["Ollama", "OpenAI", "Gemini"])
    st.session_state["provider"] = provider

    # API Keys only for cloud providers
    if provider == "OpenAI":
        st.session_state["openai_key"] = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-..."
        )

        st.session_state["model"] = st.sidebar.selectbox(
            "Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        )

    elif provider == "Gemini":
        st.session_state["gemini_key"] = st.sidebar.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza..."
        )

        st.session_state["model"] = st.sidebar.selectbox(
            "Model",
            ["gemini-1.5-pro", "gemini-1.5-flash"]
        )

    elif provider == "Ollama":
        models = get_ollama_models()
        if models:
            st.session_state["model"] = st.sidebar.selectbox("Model", models)
        else:
            st.session_state["model"] = st.sidebar.text_input("Model", "llama3.2")

# =========================================================
# STREAMLIT MAIN APP
# =========================================================
def main():
    provider_settings_interface()
    st.title("🤖 AI Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    st.write(f"**Provider:** {st.session_state.provider}")
    st.write(f"**Model:** {st.session_state.model}")

    st.markdown("---")

    # USER INPUT
    user_input = st.text_area("Your message:")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat.append({"role": "user", "content": user_input})

            # Create placeholder for streaming output
            placeholder = st.empty()
            streamed_reply = ""

            start_time = time.perf_counter()
            for token in generate_ai_response(
                st.session_state.provider,
                st.session_state.model,
                user_input
            ):
                streamed_reply += token
                placeholder.markdown(f"**Assistant:** {streamed_reply}")
            response_time = time.perf_counter() - start_time

            # Save final full message with response time
            st.session_state.chat.append({"role": "assistant", "content": streamed_reply, "response_time": response_time})

    # DISPLAY CHAT HISTORY
    st.markdown("### Conversation History")
    for msg in st.session_state.chat:
        if msg["role"] == "assistant" and "response_time" in msg:
            st.markdown(f"**Assistant:** {msg['content']}\n_Response time: {msg['response_time']:.2f} seconds_")
        elif msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")

if __name__ == "__main__":
    main()