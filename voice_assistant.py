# voice_assistant.py - Voice input/output for the skill gap identifier

from typing import Optional
from io import BytesIO
import re

# Optional dependencies
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PYTTSX3_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    SR_AVAILABLE = False

class VoiceAssistant:
    """Voice assistant for skill assessment and recommendations (with graceful fallback)"""
    
    def __init__(self):
        self.tts_available = False
        self.sr_available = False
        self.tts_engine = None
        self.recognizer = None
        
        # Initialize text-to-speech if available
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.9)
                self.tts_available = True
            except:
                self.tts_available = False
        
        # Initialize speech recognizer if available
        if SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 4000
                self.sr_available = True
            except:
                self.sr_available = False
    
    def speak(self, text: str):
        """Convert text to speech"""
        print(f"🤖 Assistant: {text}")
        if self.tts_available and self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Voice output error: {e}")
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """Listen to user voice input"""
        if not self.sr_available or not self.recognizer:
            print("Voice input not available in this environment")
            return None
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)
            
            text = self.recognizer.recognize_google(audio)
            print(f"📝 You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("Sorry, I didn't understand that")
            return None
        except sr.RequestError:
            print("Speech recognition service unavailable")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe browser-recorded audio bytes (WAV/compatible) to text."""
        if not audio_bytes or not self.sr_available or not self.recognizer:
            return None

        try:
            with sr.AudioFile(BytesIO(audio_bytes)) as source:
                audio = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None
        except Exception:
            return None

    def analyze_transcript(self, transcript: str) -> dict:
        """Lightweight voice-content analysis from transcript text."""
        if not transcript:
            return {
                "word_count": 0,
                "confidence": "Low",
                "sentiment": "Neutral",
                "complexity": "Low",
                "keywords": [],
            }

        text = transcript.lower()
        words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]*\b", text)
        word_count = len(words)
        unique_words = len(set(words))

        positive_cues = {"great", "good", "confident", "strong", "excited", "ready", "improve"}
        negative_cues = {"stuck", "hard", "difficult", "confused", "weak", "struggle", "unsure"}
        pos = sum(1 for w in words if w in positive_cues)
        neg = sum(1 for w in words if w in negative_cues)
        sentiment = "Positive" if pos > neg else "Challenging" if neg > pos else "Neutral"

        if word_count >= 10 and unique_words / max(word_count, 1) > 0.65:
            confidence = "High"
        elif word_count >= 5:
            confidence = "Medium"
        else:
            confidence = "Low"

        if word_count >= 25:
            complexity = "High"
        elif word_count >= 12:
            complexity = "Medium"
        else:
            complexity = "Low"

        stop_words = {
            "the", "a", "an", "and", "or", "to", "for", "of", "on", "in", "with", "my",
            "is", "are", "am", "i", "you", "it", "that", "this", "want", "need", "learn",
        }
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        freq = {}
        for word in keywords:
            freq[word] = freq.get(word, 0) + 1
        top_keywords = [k for k, _ in sorted(freq.items(), key=lambda item: item[1], reverse=True)[:5]]

        return {
            "word_count": word_count,
            "confidence": confidence,
            "sentiment": sentiment,
            "complexity": complexity,
            "keywords": top_keywords,
        }

    def build_subtitles(self, text: str, words_per_line: int = 10) -> list[str]:
        """Split long assistant text into subtitle-sized lines."""
        if not text:
            return []
        words = text.split()
        if not words:
            return []

        lines = []
        for index in range(0, len(words), words_per_line):
            lines.append(" ".join(words[index:index + words_per_line]))
        return lines
    
    def voice_skill_assessment(self, skills: list) -> dict:
        """Conduct voice-based skill assessment"""
        scores = {}
        
        self.speak(f"Let's assess your skills for {len(skills)} areas. Rate each from 1 to 10.")
        
        for skill in skills:
            self.speak(f"How would you rate your {skill} skill? Say a number from 1 to 10.")
            response = self.listen(timeout=15)
            
            if response:
                try:
                    # Extract number from response
                    words = response.split()
                    for word in words:
                        if word.isdigit():
                            score = int(word)
                            if 1 <= score <= 10:
                                scores[skill] = score
                                self.speak(f"Got it. {skill}: {score}")
                                break
                    else:
                        self.speak(f"I didn't catch a valid number. Setting {skill} to 5.")
                        scores[skill] = 5
                except:
                    self.speak(f"Let me set {skill} to 5 as default.")
                    scores[skill] = 5
            else:
                scores[skill] = 5
        
        return scores
    
    def voice_role_selection(self, available_roles: list) -> Optional[str]:
        """Select role through voice"""
        roles_str = ", ".join(available_roles)
        self.speak(f"Which role are you targeting? Options are: {roles_str}")
        
        response = self.listen(timeout=15)
        
        if response:
            for role in available_roles:
                if role.lower() in response.lower():
                    self.speak(f"Perfect! You selected {role}.")
                    return role
        
        self.speak("Sorry, I didn't recognize that role. Please select from the menu.")
        return None
    
    def read_gap_analysis(self, gaps: dict, readiness: float):
        """Read gap analysis results aloud"""
        self.speak(f"Your overall role readiness is {readiness} percent.")
        
        # Read top 3 priority skills
        sorted_gaps = sorted(gaps.items(), key=lambda x: x[1].get("priority_score", 0), reverse=True)
        
        if sorted_gaps:
            self.speak("Your top priority skills to develop are:")
            for i, (skill, details) in enumerate(sorted_gaps[:3], 1):
                gap = details.get("gap", 0)
                if gap > 0:
                    self.speak(f"{i}. {skill}: You need to improve by {gap} levels")
    
    def read_learning_roadmap(self, weeks: list):
        """Read learning roadmap aloud"""
        if not weeks:
            self.speak("Congratulations! You have achieved all target skills.")
            return
        
        self.speak(f"Here's your {len(weeks)} week learning plan:")
        
        for week in weeks[:2]:  # Read first 2 weeks in detail
            week_num = week.get("week", 0)
            focus_areas = week.get("focus_areas", [])
            
            if focus_areas:
                self.speak(f"Week {week_num}: Focus on {focus_areas[0]['skill']}")
                for area in focus_areas[:2]:
                    self.speak(f"{area['skill']} - Improve from level {area['current_level']} to {area['target_level']}")
    
    def confirm_voice_mode(self) -> bool:
        """Confirm if user wants to use voice mode"""
        self.speak("Would you like to use voice mode for this assessment? Say yes or no.")
        response = self.listen(timeout=10)
        
        if response and ("yes" in response or "sure" in response or "yeah" in response):
            self.speak("Great! Let's get started.")
            return True
        else:
            self.speak("Okay, we'll use the text interface instead.")
            return False
