# Music ISO-Therapy System (Cognitive & Emotional Recalibration Engine)

An empathetic, multi-agent cognitive architecture built using the Google ADK (Agent Development Kit). This system implements the clinical **ISO Principle** of music therapy, guiding users from negative or anxious states to a target emotional state (Calm or Focus) using structured music trajectories, dynamic feedback recalibration, and multilingual crisis guardrails.

---

## 🚀 Key Features

* **Empathetic Multilingual Diagnosis:** Translates natural language descriptions (English, Bengali, and Benglish code-switching) into quantitative Valence-Arousal coordinates.
* **Deterministic Trajectory Pathfinding:** Plotted using mathematical linear interpolation in the Valence-Arousal space, ensuring clinical safety and smooth emotional progression.
* **Active 12-Box Recalibration:** Analyzes user feedback after each track to adapt the remaining queue:
  * *Calmer:* Continues the planned trajectory.
  * *No Change:* Lowers arousal targets, filters out the stale genre, and boosts preferred genres.
  * *Worse:* Triggers an emergency Clinical Override, playing a deep-calm sitar/devotional rescue track and ending the session.
* **Bilingual Crisis Interceptor:** Scans user inputs using regex for self-harm keywords, instantly pausing playback and presenting localized emergency hotlines.
* **Long-Term Memory (LTM):** Persists session outcomes to adjust onboarding profiles and baseline genre preferences over time.

---

## 📐 The ISO Principle & Circumplex Model

The system operates on the **Circumplex Model of Affect**, which maps emotions across two dimensions:
1. **Valence (X-axis):** Positive vs. negative affect (from -1.0 to 1.0).
2. **Arousal (Y-axis):** High vs. low physiological energy (from -1.0 to 1.0).

```text
                        High Arousal (+1.0)
                                │
          Afraid / Anxious ░    │    ░ Joyous / Excited
          Angry / Tense    ░    │    ░ Happy / Pleased
                                │
Negative Valence (-1.0) ────────┼──────── Positive Valence (+1.0)
                                │
          Sad / Gloomy     ░    │    ░ Content / At Ease
          Depressed        ░    │    ░ Calm / Relaxed
                                │
                        Low Arousal (-1.0)
```

The **ISO Principle** states that music must first match the user's starting mood (e.g., *Angry/Tense* at `[-0.7, 0.6]`) and then gradually transition through intermediate states to guide them to a target state (e.g., *Calm/Relaxed* at `[0.75, -0.75]`).

---

## 🛠️ Architecture Overview

The system uses a collaborative multi-agent structure managed under the Google ADK:

```text
CoordinatorAgent (Orchestrator)
 ├── check_profile_tool ──► Scans user_profile.json
 ├── onboarding_tool ─────► Creates new profile if missing
 ├── DiagnosticAgent (Sub-Agent) ──► Extracts Valence-Arousal coordinates
 ├── select_goal_tool ────► Generates ISO path & queries database
 ├── get_track_tool ──────► Recommends next track (Euclidean distance + genre boost)
 ├── feedback_tool ───────► Classifies transition (Calmer / No Change / Worse)
 └── conclude_tool ───────► Logs session summary to LTM & triggers grounding exercises
```

### 1. CoordinatorAgent
The main orchestrator managing the state machine. It guides the user through onboarding, diagnostic check-in, playlist playback, feedback/recalibration, and session wrap-up.

### 2. DiagnosticAgent
A sub-agent configured to analyze free-text descriptions of user emotions, mapping the user's language to one of 12 emotional sectors in the circumplex model.

### 3. Deterministic Tools
* **Trajectory Calculator:** Performs step-by-step vector interpolation.
* **Track Matcher:** Searches a curated database of 50 Bengali classical, acoustic, and band tracks, applying a **15% distance reduction** for preferred genres and filtering out already-played tracks to prevent fatigue.
* **Safety Guard:** A fast regex engine checking bilingual keywords to intercept self-harm thoughts immediately.

---

## 📂 Repository Structure

* `AI_based_music_therapy_ISO_System.ipynb`: Complete Jupyter Notebook containing the full implementation, automated test suites, and simulation runs.
* `music_therapy_agent/`:
  * `agent.py`: Core ADK agent configuration and tools definition (exposed for local web server deployment).
  * `__init__.py`: Package initialization.
* `bengali_music_db.csv`: The curated music database with track IDs, metadata, Valence-Arousal values, and YouTube links.
* `user_profile.json`: Local JSON database representing the user's Long-Term Memory (LTM).
* `Context/Music_ISO_Therapy_Writeup.md`: Drafted Kaggle write-up submission for the *Agents for Good* track.

---

## ⚙️ Setup & Installation

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd AI_based_music_therapy
```

### 2. Configure Environment
Create a `.env` file in the root directory and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

### 3. Install Dependencies
Set up your virtual environment and install the required libraries:
```bash
python3 -m venv venv
source venv/bin/activate
pip install google-adk pandas numpy nest-asyncio python-dotenv
```

### 4. Running the Jupyter Notebook
Open the notebook in your environment:
```bash
jupyter notebook AI_based_music_therapy_ISO_System.ipynb
```
Run the cells sequentially to run the full simulation loops (Stress-to-Calm, Excited-to-Focus, No-Change recalibration, and Worse-state rescue overrides) and run the automated verification tests.

### 5. Launching the Local ADK Web UI
Launch the interactive web-based chat interface to experience the therapy system:
```bash
adk web
```
This starts the local web server. Open the displayed local URL in your browser to interact with the therapist coordinator.

---

## 🧪 Testing & Verification

The project includes built-in verification mechanisms to ensure stability and safety:
* **Automated Tests:** Validate path calculation limits, clamping bounds, crisis keyword regex triggers, and JSON database read/write integrity.
* **Clinical Safety Tests:** Test self-harm phrases in English, Bengali script, and transliterated Benglish to ensure crisis hotlines are served and music is safely halted.

---

## 👥 Author

**Bisnu Sarkar**  
ML Engineer, IQVIA  
*Kaggle Capstone Project - Agents for Good Track*