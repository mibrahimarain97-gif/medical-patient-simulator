# action_mapper.py - Simplified Action Mapping for Avatar Animations

import re
from typing import List, Dict, Any

class ActionMapper:
    def __init__(self):
        # Action detection patterns (include common variants and synonyms)
        self.action_patterns = {
            'wave': r"\b(wave|waving|hand(?:s)?|finger(?:s)?|thumb(?:s)?|arm(?:s)?|wrist(?:s)?|elbow(?:s)?|shoulder(?:s)?|forearm|upper\s*arm)\b",
            'leg': r"\b(leg|legs|hip(?:s)?|thigh(?:s)?|calf|calves|shin(?:s)?|knee(?:s)?|ankle(?:s)?|heel(?:s)?|foot|feet|toe(?:s)?)\b",
            'headache': r"\b(headache|head\s*ache|migraine(?:s)?|head\s*(pain|hurts|pounding|throbbing|pressure|tight|heavy)|temple(?:s)?|forehead\s*(pain|hurts))\b",
            'itch': r"\b(itch|itchy|itching|itches|scratch(?:ing)?|rash(?:es)?|hives|spots?)\b",
            'fever': r"\b(fever|feverish|high\s*temp(?:erature)?|temperature|hot|burning\s*up|night\s*sweats?|chills?|shiver(?:ing)?|sweat(?:ing)?)\b|\b(1(00|01|02|03|04)f|38(?:\.[0-9])?|39(?:\.[0-9])?|40(?:\.[0-9])?|degrees)\b",
            'stomach': r"\b(stomach(?:-?ache(?:s)?)?|stomach\s*ache(?:s)?|tummy|belly|bellyache(?:s)?|abdomen|abdominal|gut|indigestion|cramps?|cramping|bloating|bloated|gastric|gastritis|ulcer|reflux|heartburn|diarrh(o|h)ea|diarrhea|constipation|flatulence|gas|wind)\b",
            'chest': r"\b(chest|sternum|ribcage|thoracic|chest\s*(pain|hurts|ache|tight(ness)?|pressure)|shortness\s*of\s*breath|breathless|hard\s*to\s*breathe|wheez(?:e|ing)|lungs?|palpitation(?:s)?|heart(?:\s*(pain|racing|pounding|flutter)))\b",
            'dizzy': r"\b(dizzy|dizziness|light\s*headed|lightheaded|vertigo|faint(?:ing)?|woozy|wobbly|unsteady|spinning)\b",
            'cough': r"\b(cough|coughs|coughing|hacking|phlegm|mucus|sputum|throat\s*clearing|sore\s*throat|hoarse|hoarseness)\b",
            'sneeze': r"\b(sneeze|sneezes|sneezing|achoo|a-?choo|runny\s*nose|stuffy\s*nose|blocked\s*nose|congest(?:ed|ion)\s*nose|sniffl(?:e|ing))\b",
            'nausea': r"\b(nausea|nauseous|queasy|vomit(?:ing)?|throw(?:ing)?\s*up|retching|puking|motion\s*sickness|car\s*sick|sea\s*sick|food\s*poisoning)\b",
            'blood': r"\b(blood|bleed(?:ing)?|bloody|hematoma|laceration|bruise|bruising|cut|wound|nosebleed|coughing\s*blood|spitting\s*blood|blood\s*in\s*(stool|urine|pee|vomit))\b",
        }
    
    def analyze_message(self, message: str) -> List[str]:
        """
        Analyze a message and detect action keywords.
        Returns a list of unique actions found in the message.
        """
        detected_actions = []
        message_lower = message.lower()
        
        for action, pattern in self.action_patterns.items():
            if re.search(pattern, message_lower):
                detected_actions.append(action)
        
        # Remove duplicates within the same message but preserve order
        unique_actions = list(dict.fromkeys(detected_actions))
        
        print(f"[ActionMapper] Actions detected in message: {unique_actions}")
        return unique_actions

# Global instance
action_mapper = ActionMapper()

def process_patient_message(message: str) -> Dict[str, Any]:
    """
    Process a patient message and detect actions.
    """
    # Detect actions in the message
    actions = action_mapper.analyze_message(message)
    
    return {
        'actions': actions,
        'message': message,
        'execution_plan': f"Will execute {len(actions)} action(s) 3 times each"
    }
