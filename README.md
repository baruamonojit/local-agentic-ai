# 🤖 Open-Source Local AI Agent Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Runtime-Ollama-black.svg)](https://ollama.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Packaged with uv](https://img.shields.io/badge/Package_Manager-uv-blueviolet.svg)](https://astral.sh/uv)

A production-ready, fully open-source AI agent architecture designed to run on **local hardware** with zero token costs and zero data leakage. 

Built using **Ollama**, **LangChain / LangGraph**, and **Streamlit**, this project demonstrates how to orchestrate autonomous local agents capable of real-time tool calling, dual-path latency routing, stateful short-term memory checkpoints, and token streaming.

---

## ⚡ Key Architectural Highlights

- **100% Local Inference:** Zero cloud model lock-in. Powered by local quantized models (`qwen`, `llama3.1`, etc.) via Ollama.
- **Dual-Path Latency Router:** Solves the notorious "agent tool inspection latency" bottleneck. Chit-chat and standard conversational queries bypass the agentic reasoning graph entirely for near-instant (<500ms) execution, while complex requests route to the autonomous tool loop.
- **Autonomous Tool Calling:** Integrated search tools (Tavily/DuckDuckGo) with sanitization and context pruning to eliminate context bloat.
- **Short-Term Memory Checkpointer:** Employs LangGraph's `InMemorySaver` to persist conversation history across interactive turns using thread-scoped execution contexts (`thread_id`).
- **Real-Time Token Streaming:** Token-by-token UI emission with programmatic filtering to hide raw function-call JSON payloads from the user output.
- **Full Observability:** Native integration with **LangSmith** for trace inspection, tool decision tracking, and token profiling.
- **Modern Python Tooling:** Managed with Astral's `uv` for reproducible environments and rapid dependency installs.

---

## 🧠 System Architecture

```text
                               ┌───────────────────────────┐
                               │        User Prompt        │
                               └─────────────┬─────────────┘
                                             │
                                    [Intent Evaluator]
                                             │
                   ┌─────────────────────────┴─────────────────────────┐
                   ▼                                                   ▼
         [Simple Chit-Chat]                                    [Action Required]
                   │                                                   │
     ┌───────────────────────────┐                       ┌───────────────────────────┐
     │   Direct Local Model      │                       │     LangGraph Agent       │
     │     (Bypass Tools)        │                       │   (Stateful Checkpoint)   │
     └─────────────┬─────────────┘                       └─────────────┬─────────────┘
                   │                                                   │
                   │                                            [Tool Selection]
                   │                                                   │
                   │                                       ┌───────────┴───────────┐
                   │                                       ▼                       ▼
                   │                               [Internal Logic]        [External Tools]
                   │                                       │                       │
                   │                                       └───────────┬───────────┘
                   │                                                   │
                   └─────────────────────┬─────────────────────────────┘
                                         ▼
                            [Token Streaming Output]
                                         │
                             ┌───────────────────────┐
                             │  Streamlit UI / CLI   │
                             └───────────────────────┘