# prompts_and_evaluator.py — Prompt Engine + Evaluation + Dataset Builder

import json
import os
import numpy as np
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any

# ---------------- PROMPT ENGINE ----------------
# Simplified prompt engineering using build_prompt_template function
# Removed complex PromptEngineer class to avoid duplication and confusion 


# ---------------- DATASET EXPORT ----------------
class DatasetCollector:
    def __init__(self, output_dir="datasets"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process_conversation_logs(self, log_file_path):
        conversations = []
        with open(log_file_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                conversations.append(entry)

        grouped = defaultdict(list)
        for e in conversations:
            grouped[e['conversation_id']].append(e)

        training_data = []
        for cid, msgs in grouped.items():
            msgs.sort(key=lambda x: x['timestamp'])
            persona = msgs[0]['persona']
            training_data.append({
                'conversation_id': cid,
                'persona': persona,
                'messages': [{
                    'doctor': m['doctor_message'],
                    'patient': m['patient_response'],
                    'timestamp': m['timestamp']
                } for m in msgs],
                'metadata': {
                    'total_exchanges': len(msgs),
                    'duration_minutes': self._calc_duration(msgs),
                    'quality_score': self._score_quality(msgs)
                }
            })
        return training_data

    def _calc_duration(self, messages):
        if len(messages) < 2:
            return 0
        s = datetime.fromisoformat(messages[0]['timestamp'])
        e = datetime.fromisoformat(messages[-1]['timestamp'])
        return round((e - s).total_seconds() / 60, 2)

    def _score_quality(self, messages):
        score = 0
        l = len(messages)
        if 8 <= l <= 15:
            score += 3
        elif 5 <= l <= 20:
            score += 2
        if len(set(' '.join(m['doctor_message'].lower().split()) for m in messages)) > 50:
            score += 1
        avg_len = sum(len(m['patient_response'].split()) for m in messages) / l
        if 15 <= avg_len <= 50:
            score += 1
        return min(score, 5)

    def export_for_finetuning(self, training_data, format_type="openai"):
        if format_type == "openai":
            filename = f"{self.output_dir}/finetune_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(filename, 'w') as f:
                for conv in training_data:
                    if conv['metadata']['quality_score'] >= 3:
                        for i, msg in enumerate(conv['messages']):
                            context = conv['messages'][:i]
                            context_str = "\n".join([f"Doctor: {c['doctor']}\nPatient: {c['patient']}" for c in context])
                            f.write(json.dumps({
                                "messages": [
                                    {"role": "system", "content": f"You are a patient named {conv['persona']['name']} with chest pain."},
                                    {"role": "user", "content": f"Context:\n{context_str}\n\nDoctor: {msg['doctor']}"},
                                    {"role": "assistant", "content": msg['patient']}
                                ]
                            }) + '\n')
            return filename


# ---------------- SIMULATION EVALUATOR ----------------
class PatientSimulationEvaluator:
    def evaluate_conversation(self, conv_data, persona):
        msgs = conv_data.get('messages', [])
        if not msgs:
            return {"overall_score": 0, "reason": "No messages"}
        patient_responses = [m['patient'] for m in msgs]
        doctor_qs = [m['doctor'] for m in msgs]
        return {
            'overall_score': round(self._score_realism(patient_responses) + self._score_engagement(patient_responses, doctor_qs), 2),
            'criterion_scores': {
                'realism': self._score_realism(patient_responses),
                'engagement': self._score_engagement(patient_responses, doctor_qs)
            },
            'conversation_stats': {
                'exchanges': len(msgs),
                'avg_response_length': np.mean([len(p.split()) for p in patient_responses]),
                'patient_questions': sum(1 for r in patient_responses if '?' in r)
            }
        }

    def _score_realism(self, responses):
        clinical_terms = ["myocardial infarction", "dyspnea", "tachycardia"]
        lay_terms = ["chest pain", "can't breathe", "pressure"]
        score = 0
        if all(not any(term in r.lower() for term in clinical_terms) for r in responses):
            score += 2
        if any(any(term in r.lower() for term in lay_terms) for r in responses):
            score += 2
        if any(word in r.lower() for r in responses for word in ['worried', 'scared', 'anxious']):
            score += 1
        return min(score, 5)

    def _score_engagement(self, responses, questions):
        score = 0
        if sum(1 for r in responses if '?' in r) >= 2:
            score += 2
        avg_len = np.mean([len(r.split()) for r in responses])
        if 10 <= avg_len <= 40:
            score += 2
        unique_starts = len(set(r.split()[0].lower() for r in responses if r.split()))
        if unique_starts >= len(responses) * 0.5:
            score += 1
        return min(score, 5)

def build_prompt_template(persona, condition_name, symptoms):
    """
    Build a dynamic prompt template for patient simulation
    """
    # Separate primary (defining) symptoms from secondary symptoms
    primary_symptoms = []
    secondary_symptoms = []
    
    # Define which symptoms are primary/defining for each condition
    primary_symptom_keywords = {
        'Migraine': ['throbbing pain', 'headache', 'one side', 'zigzag', 'flashing lights'],
        'Asthma': ['wheezing', 'shortness of breath', 'chest tight'],
        'Appendicitis': ['pain', 'right side', 'abdomen', 'appendix'],
        'Food allergy': ['swelling', 'hives', 'rash', 'itching'],
        'Diabetes': ['thirsty', 'peeing', 'tired', 'weight loss'],
        'COVID-19': ['fever', 'cough', 'loss of smell', 'taste'],
        'Flu': ['fever', 'aching body', 'tired', 'cough'],
        'Tonsillitis': ['sore throat', 'swallowing', 'tonsils'],
        'Ear infections': ['earache', 'ear pain', 'hearing'],
        'Constipation': ['poo', 'bowel', 'straining'],
        'Chickenpox': ['rash', 'spots', 'itchy'],
        'Hay fever': ['sneezing', 'runny nose', 'itchy eyes'],
        'Insomnia': ['sleep', 'awake', 'tired'],
        'Heartburn': ['burning', 'chest', 'acid', 'reflux']
    }
    
    # Categorize symptoms based on condition
    if condition_name in primary_symptom_keywords:
        keywords = primary_symptom_keywords[condition_name]
        for symptom in symptoms:
            if any(keyword.lower() in symptom.lower() for keyword in keywords):
                primary_symptoms.append(symptom)
            else:
                secondary_symptoms.append(symptom)
    else:
        # Default: first 2-3 symptoms are primary, rest are secondary
        primary_symptoms = symptoms[:min(3, len(symptoms))]
        secondary_symptoms = symptoms[min(3, len(symptoms)):]
    
    prompt = f"""You are role-playing as a patient named {persona.get('name', 'Patient')} during a medical consultation.

**YOUR CHARACTER:**
- Personality: {persona['personality_traits']}
- Communication style: {persona['communication_style']}
- Background: {persona.get('age', 'Unknown')} year old {persona.get('occupation', 'person')}
- Behavior: {persona['behavior_notes']}

**YOUR MEDICAL CONDITION:**
- You have: {condition_name}

**YOUR SYMPTOMS:**
- Main symptoms (most important): {', '.join(primary_symptoms)}
- Other symptoms: {', '.join(secondary_symptoms) if secondary_symptoms else 'None'}

**HOW TO ACT:**
1. Stay in character as {persona.get('name', 'Patient')} throughout the conversation
2. Express your personality naturally - show your traits through how you speak and behave
3. Describe your symptoms naturally in conversation, not as a list
4. Use everyday language, not medical terms
5. Respond to the doctor's questions conversationally
6. Show appropriate emotions based on your personality and symptoms
7. Ask questions a real patient would ask

**IMPORTANT RULES:**
- Only mention symptoms you actually have from the list above
- Don't diagnose yourself or use medical terminology
- When the doctor gives the correct diagnosis ({condition_name}), thank them and end naturally
- When the doctor gives a wrong diagnosis, ask questions and provide more symptom details
- Keep responses natural and conversational
- Don't hallucinate symptoms or conditions that are not in the list above
- Do NOT ask for treatments, treatment plans, or next steps once correct diagnosis is given
- When correctly diagnosed, end with simple thank you: "Thank you doctor", "Thanks doc", "Thankyou doctor", "Thankyou doctor for helping me", "Thanks doc, you have been a great help"
- IMPORTANT: Only end the conversation with thank you AFTER the doctor has given the correct diagnosis
- **RESPONSE LENGTH: Keep your responses to 200 words maximum in a single message**

**EXAMPLE RESPONSES:**
- "I've been having this terrible headache on the left side of my head..."
- "It's been going on for about a week now..."
- "I'm really worried because it's affecting my work..."
- "Could you explain what might be causing this?"

Remember: You're a real person seeking medical help. Act naturally and stay true to your character!"""
    
    return prompt
