

### **Project Blueprint: Multi-Agent Bengali Music ISO-Therapy System**

**Project Objective (Phase 1 MVP):** To build a stateful, multi-agent system that utilizes the clinical ISO principle to guide users from acute stress to a calm state using a highly curated database of traditional Bengali music. The MVP will rely on manually labeled metadata to ensure rapid development within a 15-day sprint, focusing entirely on agentic orchestration, memory, and tool calling.

#### **Why We Reached This Architecture (The 15-Day Strategy)**

1. **Scope Mitigation:** Building an audio streaming server or a complex multimodal vision pipeline (spectrograms) from scratch introduces high engineering risk. Deferring the spectrograms to a Phase 2 update guarantees the core orchestration is completed on time.
2. **Domain Focus:** Relying on a tightly curated list of 15-20 tracks (featuring artists like Rabindranath Tagore or acoustic covers of Mohiner Ghoraguli) allows for precise, culturally resonant emotional mapping without needing a massive data-engineering pipeline.
3. **Meeting Capstone Criteria:** By focusing on labeled data, development time shifts completely to building the conversational memory, state management, and Python tool-calling required by the grading rubric.

---

### **System Architecture (For Antigravity Implementation)**

#### **1. The Data Layer (Local CSV/JSON Database)**

A lightweight, static database acting as the agent's environment.

* **Columns Required:** `Track_ID`, `Artist`, `Title`, `YouTube_URL`, `Acoustic_Energy_Score` (0.0 to 1.0), `Valence_Score` (0.0 to 1.0), and `Therapeutic_Tag` (e.g., "High Tension", "Transition", "Deep Calm").

#### **2. The Clinical Orchestrator Agent**

The primary interface handling user interaction and session state.

* **Role:** Engages the user in a reflective conversation or a short questionnaire to evaluate their current emotional state.
* **Capabilities:** Utilizes short-term memory to maintain context and maps the user's unstructured input into a numerical "Current Mood Score".

#### **3. The ISO-Principle Orchestration Skill (Python Tool)**

A deterministic backend tool called by the Orchestrator Agent.

* **Role:** Replaces LLM "guessing" with clinical logic.
* **Mechanism:** The Agent passes the "Current Mood Score" and a "Target Mood Score" to this Python function. The script calculates a mathematical step-by-step trajectory, queries the local database for tracks matching those specific energy/valence scores, and returns a sequenced list of YouTube URLs.

#### **4. Phase 2 Future Scope (To be implemented post-MVP)**

* **The Acoustic Profiler Agent:** Once the MVP is stable, replace the manual database labels with an automated pipeline. This secondary agent will ingest mel-spectrogram images of the tracks and use vision capabilities alongside lyric context to dynamically populate the `Acoustic_Energy_Score` and `Valence_Score`.

---

**Developer Note for Antigravity:** *Start by creating the mock CSV dataset first, then build the Python ISO-calculating function as an independent script. Once those two components are tested locally, wrap them as a Tool/Skill and attach them to the Orchestrator Agent.*