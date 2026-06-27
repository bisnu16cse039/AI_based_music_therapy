# Bengali Music Data Labeling Guide

This is a lightweight guide for annotating Bengali tracks for the **ISO-therapy system**.

---

## 1. Database Schema

Tracks are stored in [bengali_music_db.csv](file:///Users/bisnuchandrasarkar/Developer/Projects/agentic_ai/AI_based_music_therapy/Data/bengali_music_db.csv) using these columns:

| Column Name | Type | Description / Constraints |
| :--- | :--- | :--- |
| `track_id` | String | Unique ID (`track_01`, `track_02`, etc.) |
| `title` | String | Track title (English phonetics) |
| `artist` | String | Artist, singer, or band name |
| `genre` | String | Must be: `Rabindra Sangeet`, `Nazrul Geeti`, `Folk & Baul`, `Modern Acoustic`, `Bengali Band`, `Old Movie Songs` |
| `is_instrumental` | Boolean | `true` or `false` |
| `mood_tags` | String | Comma-separated list selected **only** from the Approved Dropdown Tags |
| `tempo_bpm` | Integer | *Do not fill. Calculated programmatically via audio analysis (librosa).* |
| `valence` | Float | Normalized valence score $[-1.0, 1.0]$. Formula: `(Valence_Rating - 5) / 4` |
| `arousal` | Float | Normalized arousal score $[-1.0, 1.0]$. Formula: `(Arousal_Rating - 5) / 4` |
| `youtube_url` | String | Playback link |
| `description` | String | Brief clinical description of the song's energy and emotional effect |

---

## 2. Approved Mood Tags (Dropdown Options)

To ensure consistent categorization, labelers must choose tags *only* from this predefined list, which is also stored as a reusable configuration file in [approved_mood_tags.json](file:///Users/bisnuchandrasarkar/Developer/Projects/agentic_ai/AI_based_music_therapy/Data/approved_mood_tags.json).

### Quadrant-Categorized Tags
| Quadrant | Valence / Arousal | Approved Tags (Select all that apply) |
| :--- | :--- | :--- |
| **Q1: Joyful / Energetic** | Positive V, High A | `joyful`, `energetic`, `celebratory`, `hopeful`, `uplifting`, `playful` |
| **Q2: Tense / Agitated** | Negative V, High A | `tense`, `angry`, `anxious`, `overwhelmed`, `agitated`, `dramatic` |
| **Q3: Sad / Melancholic** | Negative V, Low A | `sad`, `melancholic`, `somber`, `lonely`, `longing` |
| **Q4: Calm / Meditative** | Positive V, Low A | `calm`, `peaceful`, `serene`, `spiritual`, `comforting`, `soothing` |
| **Neutral / Transitional** | Neutral V or A | `reflective`, `nostalgic`, `bittersweet`, `philosophical` |

### Flat List of All Tags (28 Tags total)
```text
joyful, energetic, celebratory, hopeful, uplifting, playful, tense, angry, anxious, overwhelmed, agitated, dramatic, sad, melancholic, somber, lonely, longing, calm, peaceful, serene, spiritual, comforting, soothing, reflective, nostalgic, bittersweet, philosophical
```


---

## 3. Labeling Rules & Anchor Tracks

### Rating Scale (1 to 9)
Labelers rate Valence and Arousal on a scale of **1 to 9** (5 is completely neutral). 
*   **Arousal:** Based *only* on acoustic speed/intensity (loudness, tempo). 
*   **Valence:** Based on musical key (major/minor) and lyric sentiment. For upbeat songs with sad lyrics, rate arousal high and valence neutral-to-low.

### Anchor Tracks for Calibration

```text
                               Arousal (9)
                                    │
                                    │   [Q1] "Komola Shundori" (Folk)
            [Q2] "Trishula" (Band)  │   - Valence: 7-8 | Arousal: 7-8
            - Valence: 2-3          │
            - Arousal: 7-8          │
                                    │
Valence (1) ────────────────────────┼──────────────────────── Valence (9)
                                    │
            [Q3] "Amaro Porano"     │   [Q4] "Anandoloke Mongololoke" (Puja RS)
            - Valence: 2-3          │   - Valence: 8-9 | Arousal: 2-3
            - Arousal: 2-3          │
                                    │
                               Arousal (1)
```

| Quadrant | Target (V, A) | Example Bengali Anchor Track |
| :--- | :--- | :--- |
| **Q1: Joyful/Energetic** | `(+0.50, +0.50)` to `(+0.75, +0.75)` | *"Komola Shundori"* (Upbeat Folk) or *"Prithibita Naki Chhoto"* |
| **Q2: Tense/Agitated** | `(-0.75, +0.75)` | *"Trishula"* (Fossils - Bengali Band) |
| **Q3: Sad/Melancholic** | `(-0.75, -0.75)` | *"Amaro Porano Jaha Chay"* (Melancholic Rabindra Sangeet) |
| **Q4: Calm/Meditative** | `(+0.75, -0.75)` to `(+1.00, -0.50)` | *"Anandoloke Mongololoke"* (Calm Rabindra Sangeet) |

---

## 4. Dataset Balance Requirements
*   Minimum **20 tracks** total.
*   At least **5 tracks** per emotional quadrant.
*   At least **2-3 tracks** (10-15%) must be instrumental (`is_instrumental: true`).
