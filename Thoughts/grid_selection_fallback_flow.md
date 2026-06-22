# UX Design: Conversational LLM Fallback for 9x9 Affect Grid Selection

This document designs a seamless fallback path for when users are confused by the 9x9 Affect Grid or unsure how to locate their current emotional state on it.

---

## 1. The Core Problem: Grid Cognitive Load
While the 9x9 Affect Grid is a powerful, single-click input tool, it can introduce cognitive load for users who are:
*   Experiencing acute stress or panic (making coordinates hard to comprehend).
*   Unfamiliar with the psychological concepts of *Valence* (pleasantness) and *Arousal* (energy activation).
*   Unsure how to map mixed emotions (e.g., "angry but tired").

---

## 2. The Solution: Hybrid UI (Mood Tags + Optional Text Box)

Instead of forcing users to either guess on the grid or write a long open-ended explanation, we introduce a **Hybrid Fallback Interface**:

1.  **Pre-defined Quick-Select Mood Tags:** Visually clickable "chips" representing common emotional states.
2.  **Optional Open-Ended Text Box:** A space for the user to add optional detail (e.g., *"Why do you feel this way?"* or *"Anything else?"*).

### UI/UX Flow
```text
┌────────────────────────────────────────────────────────┐
│               User is on the 9x9 Grid UI               │
└───────────────────────────┬────────────────────────────┘
                            │
              User clicks "Help me choose"
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Display Fallback Selection Dialog          │
│                                                        │
│   [Overwhelmed] [Burned Out] [Restless] [Sad/Gloomy]   │
│   [Tired/Heavy] [Anxious/Tense] [Calm/Okay]            │
│                                                        │
│   Text Box: "Or describe in your own words..."         │
└───────────────────────────┬────────────────────────────┘
                            │
             User selects a Tag and/or enters Text
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Diagnostic Agent parses inputs            │
│  * If Tag only: Uses hardcoded coordinate.             │
│  * If Text included: LLM refines coordinate based on   │
│    the text nuance.                                    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│        Grid UI Autofills & Highlights the Cell         │
│   "I've highlighted this cell on the grid for you.      │
│   Does this feel right?"                               │
└───────────────────────────┬────────────────────────────┘
                            │
             ┌──────────────┴──────────────┐
     User clicks "Confirm"         User manually adjusts cell
             │                             │
             ▼                             ▼
   ┌───────────────────┐         ┌───────────────────┐
   │ Submit Coordinate │         │ Submit Coordinate │
   └───────────────────┘         └───────────────────┘
```

---

## 3. Step-by-Step Conversational Path

### Step 1: Triggering the Fallback
A button labeled **"Unsure? Let's talk it out"** is placed directly below the 9x9 grid. Clicking this opens a modal displaying the hybrid interface.

### Step 2: The Hybrid Interface Structure
The user is presented with:
*   **A selection of 6 quick-select tags (mapped to baseline coordinates):**
    *   `Overwhelmed / Stressed`: maps to $V = -0.6$, $A = +0.8$
    *   `Anxious / Jittery`: maps to $V = -0.5$, $A = +0.6$
    *   `Tired / Heavy`: maps to $V = -0.4$, $A = -0.7$
    *   `Sad / Gloomy`: maps to $V = -0.7$, $A = -0.4$
    *   `Burned Out / Numb`: maps to $V = -0.5$, $A = -0.6$
    *   `Calm / Okay`: maps to $V = +0.4$, $A = -0.4$
*   **An optional text area:** `"Want to share more detail? (e.g. 'I'm anxious about my presentation today')"`

### Step 3: Coordinates Parsing (Backend Logic)
The system evaluates the inputs as follows:

```python
def resolve_coordinates(tag=None, user_text=""):
    # 1. Start with baseline coordinate from clicked tag (if any)
    if tag:
        coords = get_tag_coordinates(tag)
    else:
        coords = (0.0, 0.0) # Start from neutral if no tag selected
        
    # 2. If user provided text, use the LLM to refine the coordinates
    if user_text.strip():
        # The LLM receives the base tag and the user's text to compute the delta
        refined_coords = call_diagnostic_agent(base_coords=coords, text=user_text)
        return refined_coords
        
    return coords
```

*Example Output from LLM Refinement:*
If user clicks `Anxious / Jittery` (base $V = -0.5$, $A = +0.6$) but types: *"My heart is racing so fast and I feel like I'm having a panic attack"*, the LLM increases arousal to $A = +0.9$ and decreases valence to $V = -0.8$, outputting:
```json
{
  "valence_score": -0.8,
  "arousal_score": 0.9,
  "detected_mood": "panic/acute anxiety"
}
```

### Step 4: Visual Auto-Positioning
The system takes the final `valence_score` and `arousal_score` and maps them back to the grid coordinate:
*   $$\text{Column} = \text{round}(V \times 4 + 5)$$
*   $$\text{Row} = \text{round}(A \times 4 + 5)$$

The corresponding cell is highlighted on the screen.

### Step 5: User-in-the-Loop Confirmation (HITL)
To keep the user in control, the system prompts:
*   *UI message:* `"I've highlighted a spot for you on the grid based on your selections. You can click 'Confirm & Start Music' or click any other box on the grid if you'd like to adjust it."`

---

## 4. Why This Works Clinically and Technically
1.  **Reduces Friction:** The user gets the benefit of a natural conversational interface without losing the accuracy of the mathematical grid coordinates.
2.  **User Agency:** The user still has the final say (they can override the LLM's recommendation by clicking a different square on the grid).
3.  **Clean State Management:** The rest of the system (the sequential coordinator and trajectory planner) only has to deal with one unified input source: a grid coordinate.

---

## 5. Grid Onboarding & Micro-Copy Context

To prevent confusion when the user first sees the 9x9 grid, the UI must provide clear visual labels and minimal instruction copy.

### A. Minimal Onboarding Copy (Displayed Above Grid)
*   **Headline:** `"Where is your mood right now?"`
*   **Sub-headline:** `"Tap anywhere on the grid below. The further right you click, the more pleasant you feel. The higher up you click, the more energetic you feel. If you're unsure, tap 'Help me choose' below."`

### B. Visual Grid Labels (Embedded Cues)
Rather than displaying a blank grid, we place simple, intuitive labels directly around and inside the grid borders:

*   **Axis Labels:**
    *   **Right Side:** `Pleasant →`
    *   **Left Side:** `← Unpleasant`
    *   **Top:** `High Energy / Alert` (pointing up)
    *   **Bottom:** `Low Energy / Calm` (pointing down)
*   **Corner Mood Indicators (Small, faded text in the corners):**
    *   **Top-Left:** `Stressed / Frustrated`
    *   **Top-Right:** `Excited / Happy`
    *   **Bottom-Left:** `Tired / Sad`
    *   **Bottom-Right:** `Calm / Relaxed`

By labeling the corners, the grid becomes self-explanatory. The user does not need to understand "valence" or "arousal" terminology; they simply click closer to the corner descriptor that matches their current emotional state.

