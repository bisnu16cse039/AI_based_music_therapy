import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from google import adk
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

load_dotenv()

# Model configuration
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Database & Profile paths
DB_NAME = 'bengali_music_db.csv'
PROFILE_PATH = "user_profile.json"

# Load database
try:
    df = pd.read_csv(DB_NAME)
except Exception:
    df = pd.DataFrame()

# ----------------------------------------------------
# Core functions & LTM management
# ----------------------------------------------------

def load_user_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_user_profile(profile):
    try:
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profile, f, indent=2)
    except Exception:
        pass

def create_user_profile(gad2_score, preferred_genre):
    profile = {
        "user_id": "user_01",
        "baseline": {
            "gad2_score": gad2_score,
            "preferred_genre": preferred_genre,
            "created_at": datetime.now().isoformat()
        },
        "session_history": []
    }
    save_user_profile(profile)
    return profile

def add_session_to_history(session_summary):
    profile = load_user_profile()
    if profile is not None:
        profile["session_history"].append(session_summary)
        save_user_profile(profile)

def generate_trajectory(start_coords, target_coords, steps=3):
    v_start, a_start = start_coords
    v_target, a_target = target_coords
    
    trajectory = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 1.0
        v_i = v_start + (v_target - v_start) * t
        a_i = a_start + (a_target - a_start) * t
        
        # Clamp values to [-1.0, 1.0] range
        v_i_clamped = max(-1.0, min(1.0, v_i))
        a_i_clamped = max(-1.0, min(1.0, a_i))
        
        trajectory.append((round(v_i_clamped, 3), round(a_i_clamped, 3)))
        
    return trajectory

def match_track_to_coordinate(valence_target, arousal_target, db_df, preferred_genre=None, played_ids=None):
    if played_ids is None:
        played_ids = set()
        
    best_track = None
    min_dist = float('inf')
    
    for idx, row in db_df.iterrows():
        track_id = row['track_id']
        
        if track_id in played_ids:
            continue
            
        v_diff = row['valence'] - valence_target
        a_diff = row['arousal'] - arousal_target
        raw_dist = np.sqrt(v_diff**2 + a_diff**2)
        
        is_preferred = (preferred_genre is not None) and (row['genre'] == preferred_genre)
        final_dist = raw_dist * 0.85 if is_preferred else raw_dist
        
        if final_dist < min_dist:
            min_dist = final_dist
            best_track = row.to_dict()
            
    return best_track

def safety_guard_skill(user_input: str) -> dict:
    HIGH_SEVERITY_TERMS = {
        "suicide", "suicidal", "kill myself", "end it all", "want to die", "better off dead", 
        "overdose", "self-harm", "cutting", "harm myself", "goodbye forever", "no one will miss me",
        "kms", "sui", "self delete", "unalive", "end my life",
        "আত্মহত্যা", "আত্মঘাতী", "মরে যাবো", "মরতে চাই", "জীবন শেষ", "বাঁচতে চাই না", "ফাঁস", "বিষ খাবো",
        "ami more jabo", "suicide korbo", "self harm korchi", "die kore felbo",
        "ami morbo", "more jete", "mora jete", "attahatya", "atmohottya", "bachbo na", "jeebon sesh", "sob sesh"
    }

    LOWER_SEVERITY_TERMS = {
        "worthless", "burden", "hopeless", "helpless", "trapped", "nothing left", "can't go on", "no point living",
        "life e kono mane nei", "ami burden", "depression e more jacchi", "kono hope nei", "family re burden"
    }

    PERSONAL_CONTEXT_MARKERS = {
        "i feel", "feel", "my life", "life e", "আমি", "আমার", "আমার ভালো", "মনটা", "নিজেকে"
    }

    ALLOW_LIST_WORDS = {
        "song", "lyrics", "music", "sing", "singing", "album", "artist", "track", "gan", "gaan", "sangeet"
    }

    cleaned = user_input.lower().strip()
    
    for word in ALLOW_LIST_WORDS:
        if word in cleaned:
            return {"crisis_detected": False, "hotlines": {}}
            
    for term in HIGH_SEVERITY_TERMS:
        if term in cleaned:
            return {
                "crisis_detected": True,
                "hotlines": {
                    "Bangladesh Primary (Kaan Pete Roi)": "Phone: +880-9612-119911, +880-1779-553399 (Daily 3PM - 3AM)",
                    "India Primary (Vandrevala Foundation)": "Phone: +91-9999-666-555 (24/7 Toll-free)",
                    "Global Suicide Hotlines": "https://findahelpline.com/"
                }
            }
            
    lower_trigger = False
    for term in LOWER_SEVERITY_TERMS:
        if term in cleaned:
            lower_trigger = True
            break
            
    if lower_trigger:
        context_matched = False
        for marker in PERSONAL_CONTEXT_MARKERS:
            if marker in cleaned:
                context_matched = True
                break
        
        found_terms = [t for t in LOWER_SEVERITY_TERMS if t in cleaned]
        
        if context_matched or len(found_terms) >= 2:
            return {
                "crisis_detected": True,
                "hotlines": {
                    "Bangladesh Primary (Kaan Pete Roi)": "Phone: +880-9612-119911, +880-1779-553399 (Daily 3PM - 3AM)",
                    "India Primary (Vandrevala Foundation)": "Phone: +91-9999-666-555 (24/7 Toll-free)",
                    "Global Suicide Hotlines": "https://findahelpline.com/"
                }
            }
            
    return {"crisis_detected": False, "hotlines": {}}

# ----------------------------------------------------
# Global Session State
# ----------------------------------------------------
session_state = {
    "session_id": "session_web_run",
    "user_id": "user_01",
    "baseline_loaded": False,
    "preferred_genre": None,
    "gad2_score": None,
    "current_mood": None,
    "current_coords": None,
    "target_coords": None,
    "goal_type": None,
    "trajectory": None,
    "playlist": [],
    "played_ids": set(),
    "current_step": 0,
    "transitions_log": [],
    "session_active": False
}

EMOTION_COORDINATES = {
    "Afraid / Anxious": (-0.6, 0.8),
    "Angry / Tense": (-0.7, 0.6),
    "Distressed / Annoyed": (-0.8, 0.2),
    "Sad / Gloomy": (-0.7, -0.4),
    "Depressed / Miserable": (-0.6, -0.7),
    "Bored / Tired": (-0.3, -0.8),
    "Sleepy / Sluggish": (0.0, -0.9),
    "Calm / Relaxed": (0.7, -0.7),
    "Content / At Ease": (0.8, -0.3),
    "Happy / Pleased": (0.9, 0.1),
    "Joyous / Excited": (0.7, 0.6),
    "Surprised / Alert": (0.0, 0.8)
}

# ----------------------------------------------------
# Session Flow Helper Functions
# ----------------------------------------------------

def check_user_profile() -> str:
    profile = load_user_profile()
    if profile:
        session_state["baseline_loaded"] = True
        session_state["preferred_genre"] = profile["baseline"]["preferred_genre"]
        session_state["gad2_score"] = profile["baseline"]["gad2_score"]
        return f"Profile found: Preferred Genre = {session_state['preferred_genre']}, GAD-2 Score = {session_state['gad2_score']}."
    else:
        session_state["baseline_loaded"] = False
        return "No user profile found. Onboarding required."

def run_onboarding(preferred_genre: str, gad2_score: int) -> str:
    try:
        create_user_profile(gad2_score=int(gad2_score), preferred_genre=preferred_genre)
        session_state["baseline_loaded"] = True
        session_state["preferred_genre"] = preferred_genre
        session_state["gad2_score"] = int(gad2_score)
        return "Onboarding completed successfully. Profile created."
    except Exception as e:
        return f"Error completing onboarding: {e}"

def set_mood_coordinates(category: str, valence: float, arousal: float) -> str:
    session_state["current_mood"] = category
    session_state["current_coords"] = (round(float(valence), 3), round(float(arousal), 3))
    return f"Successfully registered mood: '{category}' at Valence={valence}, Arousal={arousal}."

def select_session_goal(goal_type: str) -> str:
    goal_clean = goal_type.lower().strip()
    if "calm" in goal_clean:
        session_state["goal_type"] = "calm"
        session_state["target_coords"] = (0.75, -0.75)
    elif "focus" in goal_clean or "study" in goal_clean:
        session_state["goal_type"] = "focus"
        session_state["target_coords"] = (0.50, -0.20)
    else:
        return "Error: Invalid goal. Please choose 'calm' or 'focus'."

    if not session_state["current_coords"]:
        return "Error: Current mood coordinates are not set. Run mood check-in first."
        
    trajectory = generate_trajectory(
        start_coords=session_state["current_coords"],
        target_coords=session_state["target_coords"],
        steps=3
    )
    session_state["trajectory"] = trajectory
    
    # Pre-populate initial playlist using matched tracks for each step in trajectory
    session_state["playlist"] = []
    session_state["played_ids"] = set()
    for i, coords in enumerate(session_state["trajectory"]):
        matched_track = match_track_to_coordinate(
            valence_target=coords[0],
            arousal_target=coords[1],
            db_df=df,
            preferred_genre=session_state["preferred_genre"],
            played_ids=session_state["played_ids"]
        )
        if matched_track:
            session_state["playlist"].append(matched_track)
            
    session_state["current_step"] = 0
    session_state["transitions_log"] = []
    session_state["session_active"] = True
    
    return f"Session goal set to {session_state['goal_type']}. Path generated: {trajectory}. Playlist length: {len(session_state['playlist'])} tracks."

def get_next_track_recommendation() -> str:
    if not session_state["session_active"]:
        return "Error: No active therapy session. Please select a goal first."
        
    step_index = session_state["current_step"]
    playlist = session_state["playlist"]
    
    if step_index >= len(playlist):
        return "All tracks in the current trajectory have been played. Please request the session to be concluded."
        
    track = playlist[step_index]
    session_state["played_ids"].add(track["track_id"])
    
    msg = (
        f"🎵 [PLAYING TRACK {step_index + 1} of {len(playlist)}]\n"
        f"Title: '{track['title']}'\n"
        f"Artist: {track['artist']}\n"
        f"Genre: {track['genre']} (Valence: {track['valence']}, Arousal: {track['arousal']})\n"
        f"YouTube Link: {track['youtube_url']}\n\n"
        "Please listen to the track. Once finished, describe your current mood or check in using the 12-box emotional names."
    )
    return msg

def submit_session_feedback(mood_selection: str) -> str:
    if not session_state["session_active"]:
        return "Error: No active therapy session. Please select a goal first."
        
    step_index = session_state["current_step"]
    playlist = session_state["playlist"]
    
    if step_index >= len(playlist):
        return "Error: All tracks have already been played. Please conclude the session."
        
    # Check safety
    safety_check = safety_guard_skill(mood_selection)
    if safety_check["crisis_detected"]:
        session_state["session_active"] = False
        hotlines_str = "\n".join([f"- {k}: {v}" for k, v in safety_check["hotlines"].items()])
        return f"🚨 CRISIS DETECTED!\nWe are pausing music playback immediately. Please seek help:\n{hotlines_str}"
        
    # Match mood coordinate
    clean_mood = mood_selection.lower().strip()
    selected_mood = None
    for k, v in EMOTION_COORDINATES.items():
        if k.lower() == clean_mood or clean_mood in k.lower():
            selected_mood = {"name": k, "coords": v}
            break
            
    if not selected_mood:
        return f"Error: Mood '{mood_selection}' not recognized. Please choose from: {', '.join(EMOTION_COORDINATES.keys())}"
        
    prev_coords = session_state["current_coords"]
    new_coords = selected_mood["coords"]
    prev_name = session_state["current_mood"]
    new_name = selected_mood["name"]
    
    v_prev, a_prev = prev_coords
    v_new, a_new = new_coords
    v_delta = round(v_new - v_prev, 3)
    a_delta = round(a_new - a_prev, 3)
    
    if prev_name and new_name and prev_name.lower().strip() == new_name.lower().strip():
        status = "no_change"
    else:
        dist = np.sqrt(v_delta**2 + a_delta**2)
        if dist < 0.05:
            status = "no_change"
        elif a_delta > 0.05 and v_delta <= 0.05:
            status = "worse"
        elif v_delta < -0.05 and a_delta >= -0.05:
            status = "worse"
        else:
            status = "calmer"
            
    track = playlist[step_index]
    session_state["transitions_log"].append({"step": step_index + 1, "genre": track["genre"], "status": status})
    
    set_mood_coordinates(new_name, new_coords[0], new_coords[1])
    
    recal_msg = recalibrate_session_trajectory(session_state, status, df)
    
    if status == "worse":
        rescue_track = session_state["playlist"][-1]
        session_state["session_active"] = False
        msg = (
            f"⚠️ CLINICAL OVERRIDE ACTIVATED (Status: Worse)\n"
            f"Transition analysis: User felt more agitated or distressed.\n"
            f"Emergency clinical track queued immediately: '{rescue_track['title']}' by {rescue_track['artist']}\n"
            f"YouTube Link: {rescue_track['youtube_url']}\n\n"
            "Please listen to this grounding track. We are concluding the session now. Take slow deep breaths."
        )
        return msg
        
    if status == "no_change":
        return (
            f"📊 Transition Class: NO CHANGE\n"
            f"Action: {recal_msg}\n"
            "Remaining tracks adjusted to lower arousal targets and stale genre avoided. Please request the next track."
        )
        
    session_state["current_step"] = step_index + 1
    if session_state["current_step"] >= len(session_state["playlist"]):
        return (
            f"📊 Transition Class: CALMER\n"
            "Planned trajectory is working positively! You have reached the end of the playlist. Please request to conclude the session."
        )
    else:
        return (
            f"📊 Transition Class: CALMER\n"
            "Planned trajectory is working positively! Please request the next track."
        )

def conclude_session_and_log() -> str:
    if not session_state["session_active"] and not session_state["playlist"]:
        return "Error: No session is active or has been run."
        
    transitions = session_state["transitions_log"]
    outcome = "successful" if "worse" not in [t["status"] for t in transitions] else "rescued"
    
    sim_summary = {
        "session_id": session_state["session_id"],
        "initial_coords": list(session_state["current_coords"]) if session_state["current_coords"] else [0.0, 0.0],
        "current_coords": list(session_state["current_coords"]) if session_state["current_coords"] else [0.0, 0.0],
        "goal_type": session_state["goal_type"],
        "played_ids": list(session_state["played_ids"]),
        "crisis_flagged": outcome == "rescued"
    }
    
    grounding_msg = conclude_session_and_save_ltm(sim_summary, transitions)
    session_state["session_active"] = False
    
    return (
        f"✨ [SESSION CONCLUDED - {outcome.upper()}]\n"
        "Your session progress and preferences have been securely logged to your LTM profile.\n\n"
        f"{grounding_msg}"
    )

# ----------------------------------------------------
# Active Recalibration & Grounding
# ----------------------------------------------------

def recalibrate_session_trajectory(session_state, transition_status, db_df):
    current_step = session_state.get("current_step", 0)
    playlist = session_state.get("playlist", [])
    
    if transition_status == "calmer":
        session_state["current_step"] = current_step + 1
        return "Proceeding along the planned therapeutic trajectory as the user is responding positively (Calmer)."
        
    elif transition_status == "no_change":
        last_track = playlist[current_step] if current_step < len(playlist) else None
        last_coords = (last_track["valence"], last_track["arousal"]) if last_track else session_state["current_coords"]
        
        target_v, target_a = session_state["target_coords"]
        new_target_a = max(-1.0, target_a - 0.15)
        new_target_coords = (target_v, new_target_a)
        
        total_steps = len(playlist)
        remaining_steps = total_steps - (current_step + 1)
        
        if remaining_steps <= 0:
            session_state["current_step"] = current_step + 1
            return "No Change detected, but the session is at its final step. Proceeding to conclude."
            
        new_traj = generate_trajectory(
            start_coords=last_coords,
            target_coords=new_target_coords,
            steps=remaining_steps + 1
        )
        new_traj_steps = new_traj[1:]
        
        stale_genre = last_track["genre"] if last_track else None
        
        played_ids = set(session_state.get("played_ids", set()))
        if last_track:
            played_ids.add(last_track["track_id"])
            
        new_playlist_segment = []
        for i, coords in enumerate(new_traj_steps):
            filtered_db = db_df
            if stale_genre:
                filtered_db = db_df[db_df["genre"] != stale_genre]
                if filtered_db.empty:
                    filtered_db = db_df
                    
            matched_track = match_track_to_coordinate(
                valence_target=coords[0],
                arousal_target=coords[1],
                db_df=filtered_db,
                preferred_genre=session_state.get("preferred_genre"),
                played_ids=played_ids
            )
            if matched_track:
                new_playlist_segment.append(matched_track)
                played_ids.add(matched_track["track_id"])
            else:
                matched_track_fallback = match_track_to_coordinate(
                    valence_target=coords[0],
                    arousal_target=coords[1],
                    db_df=db_df,
                    preferred_genre=session_state.get("preferred_genre"),
                    played_ids=played_ids
                )
                if matched_track_fallback:
                    new_playlist_segment.append(matched_track_fallback)
                    played_ids.add(matched_track_fallback["track_id"])
        
        updated_playlist = playlist[:current_step + 1] + new_playlist_segment
        session_state["playlist"] = updated_playlist
        session_state["played_ids"] = played_ids
        session_state["current_step"] = current_step + 1
        
        return f"No Change detected. Recalibrated remaining trajectory towards lower arousal target {new_target_coords}, avoiding stale genre '{stale_genre}'."
        
    elif transition_status == "worse":
        played_playlist = playlist[:current_step + 1]
        
        rescue_track_id = "track_02"
        if rescue_track_id in session_state.get("played_ids", set()):
            rescue_track_id = "track_24"
            
        rescue_rows = db_df[db_df["track_id"] == rescue_track_id]
        if not rescue_rows.empty:
            rescue_track = rescue_rows.iloc[0].to_dict()
        else:
            rescue_track = match_track_to_coordinate(
                valence_target=0.75,
                arousal_target=-0.75,
                db_df=db_df,
                preferred_genre=session_state.get("preferred_genre"),
                played_ids=set()
            )
            
        session_state["playlist"] = played_playlist + [rescue_track]
        session_state["current_step"] = len(session_state["playlist"]) - 1
        session_state["crisis_flagged"] = True
        
        return f"WARNING: Negative state shift detected (Worse). Intercepting session and queueing deep-calm rescue track: '{rescue_track['title']}'."
        
    return "Invalid transition status."

def generate_grounding_exercises(final_coords):
    v, a = final_coords
    if a > 0.0:
        return (
            "🧘 [Clinical Grounding Exercise: 4-7-8 Breathing]\n"
            "To help settle your active energy, let's practice the 4-7-8 breathing technique:\n"
            "1. Inhale quietly through your nose for 4 seconds.\n"
            "2. Hold your breath for a count of 7 seconds.\n"
            "3. Exhale completely through your mouth, making a whoosh sound, for 8 seconds.\n"
            "Repeat this cycle 4 times to ground your nervous system."
        )
    elif v < 0.2:
        return (
            "🌱 [Clinical Grounding Exercise: 5-4-3-2-1 Sensory Focus]\n"
            "To help ground your mind and ease feelings of somberness or isolation, let's scan your surroundings:\n"
            "- Acknowledge 5 things you can see around you.\n"
            "- Acknowledge 4 things you can touch.\n"
            "- Acknowledge 3 things you can hear.\n"
            "- Acknowledge 2 things you can smell.\n"
            "- Acknowledge 1 thing you can taste.\n"
            "Take a deep, slow breath. You are here, and you are safe."
        )
    else:
        return (
            "✨ [Clinical Grounding Exercise: Positive Stabilization]\n"
            "You have reached a serene and balanced state. Take a moment to reflect on this stability:\n"
            "1. Sit comfortably and notice the relaxed feeling in your chest and shoulders.\n"
            "2. Anchor this sensation in your memory. Whenever you feel stressed, remember this calm focus.\n"
            "We wish you a wonderful and peaceful day ahead!"
        )

def conclude_session_and_save_ltm(session_state, transition_history):
    starting_coords = session_state.get("initial_coords")
    final_coords = session_state.get("current_coords")
    
    is_rescued = session_state.get("crisis_flagged", False)
    outcome = "rescued" if is_rescued else "successful"
    
    session_summary = {
        "session_id": session_state.get("session_id", "session_unknown"),
        "date": datetime.now().isoformat(),
        "starting_coords": list(starting_coords) if starting_coords else None,
        "final_coords": list(final_coords) if final_coords else None,
        "goal_type": session_state.get("goal_type"),
        "tracks_played": list(session_state.get("played_ids", [])),
        "transition_history": transition_history,
        "outcome": outcome,
        "completed": True
    }
    
    add_session_to_history(session_summary)
    
    profile = load_user_profile()
    if profile:
        positive_genres = [h["genre"] for h in transition_history if h.get("status") == "calmer"]
        
        if positive_genres:
            from collections import Counter
            most_successful_genre = Counter(positive_genres).most_common(1)[0][0]
            
            old_preferred = profile["baseline"].get("preferred_genre")
            if most_successful_genre != old_preferred:
                profile["baseline"]["preferred_genre"] = most_successful_genre
                profile["baseline"]["updated_at"] = datetime.now().isoformat()
                print(f"📊 [LTM Baseline Adjustment]: Updated preferred genre from '{old_preferred}' to '{most_successful_genre}' based on positive shift.")
                
        history = profile.get("session_history", [])
        total_sessions = len(history)
        success_sessions = sum(1 for s in history if s.get("outcome") == "successful")
        
        profile["baseline"]["total_sessions"] = total_sessions
        profile["baseline"]["success_rate"] = round(success_sessions / total_sessions, 2) if total_sessions > 0 else 1.0
        save_user_profile(profile)
        
    grounding = generate_grounding_exercises(final_coords if final_coords else (0.0, 0.0))
    return grounding

# ----------------------------------------------------
# Session coordinator tools
# ----------------------------------------------------

def check_user_profile_tool_func() -> str:
    return check_user_profile()

def onboarding_tool_func(preferred_genre: str, gad2_score: int) -> str:
    return run_onboarding(preferred_genre, gad2_score)

def set_mood_coordinates_tool_func(category: str, valence: float, arousal: float) -> str:
    return set_mood_coordinates(category, valence, arousal)

def select_session_goal_tool_func(goal_type: str) -> str:
    return select_session_goal(goal_type)

def get_next_track_recommendation_tool_func() -> str:
    return get_next_track_recommendation()

def submit_session_feedback_tool_func(mood_selection: str) -> str:
    return submit_session_feedback(mood_selection)

def conclude_session_tool_func() -> str:
    return conclude_session_and_log()

# ----------------------------------------------------
# Agent Definitions
# ----------------------------------------------------

# Tools wrapping
check_profile_tool = FunctionTool(func=check_user_profile_tool_func)
onboarding_tool = FunctionTool(func=onboarding_tool_func)
set_mood_coordinates_tool = FunctionTool(func=set_mood_coordinates_tool_func)
select_goal_tool = FunctionTool(func=select_session_goal_tool_func)
get_track_tool = FunctionTool(func=get_next_track_recommendation_tool_func)
feedback_tool = FunctionTool(func=submit_session_feedback_tool_func)
conclude_tool = FunctionTool(func=conclude_session_tool_func)

DIAGNOSTIC_INSTRUCTIONS = """
You are an empathetic, professional clinical music therapist's assistant (Diagnostic Agent).
Your primary goal is to analyze the user's natural language mood description and extract their current Valence-Arousal coordinates.

Here is the predefined 12-box named emotional model coordinates reference:
- "Afraid / Anxious": V=-0.6, A=0.8
- "Angry / Tense": V=-0.7, A=0.6
- "Distressed / Annoyed": V=-0.8, A=0.2
- "Sad / Gloomy": V=-0.7, A=-0.4
- "Depressed / Miserable": V=-0.6, A=-0.7
- "Bored / Tired": V=-0.3, A=-0.8
- "Sleepy / Sluggish": V=0.0, A=-0.9
- "Calm / Relaxed": V=0.7, A=-0.7
- "Content / At Ease": V=0.8, A=-0.3
- "Happy / Pleased": V=0.9, A=0.1
- "Joyous / Excited": V=0.7, A=0.6
- "Surprised / Alert": V=0.0, A=0.8

CRITICAL INSTRUCTION: Map the user's input to one of the 12 categories above. Only use custom coordinates if it does not align. Call `set_mood_coordinates_tool` with category, valence, and arousal.
"""

DiagnosticAgent = Agent(
    name="DiagnosticAgent",
    model=GEMINI_MODEL,
    instruction=DIAGNOSTIC_INSTRUCTIONS,
    tools=[set_mood_coordinates_tool]
)

COORDINATOR_INSTRUCTIONS = """
You are the Therapist Session Coordinator Agent.
Your task is to manage the onboarding, mood tracking, and goal settings for the music therapy session, and then guide them track-by-track.

Workflow:
1. First, call `check_profile_tool` to inspect if the user has an existing profile.
2. If profile is missing, ask the user for their preferred genre and GAD-2 anxiety score, then call `onboarding_tool`.
3. Ask the user how they are currently feeling. Route their mood description to `DiagnosticAgent` to get their starting coordinates.
4. Ask the user for their therapy goal (either 'calm' or 'focus' / 'study') and call `select_goal_tool` with the goal.
5. After the goal is set, call `get_track_tool` to get the first track recommendation and display it (Title, Artist, Link) to the user.
6. Once the user has listened, ask them how they feel. They can enter a mood index (1-12) or description. Call `feedback_tool` with their selection to recalibrate.
7. Call `get_track_tool` to present the next track, repeating feedback check-ins.
8. After the final track, call `conclude_tool` to save progress to LTM and print the concluding exercises.

Be warm, empathetic, and guide the user through these steps sequentially in conversation.
"""

CoordinatorAgent = Agent(
    name="CoordinatorAgent",
    model=GEMINI_MODEL,
    instruction=COORDINATOR_INSTRUCTIONS,
    tools=[check_profile_tool, onboarding_tool, select_goal_tool, get_track_tool, feedback_tool, conclude_tool],
    sub_agents=[DiagnosticAgent]
)

# Expose CoordinatorAgent as root_agent for adk web UI discovery
root_agent = CoordinatorAgent
