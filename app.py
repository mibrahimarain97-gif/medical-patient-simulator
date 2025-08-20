from flask import Flask, render_template, request, jsonify, session, redirect
import os
import json
import random
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import uuid
from prompts_and_evaluator import build_prompt_template
from action_mapper import process_patient_message, action_mapper
import pandas as pd

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")

# Configure OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)

# Remove environment variable model selection
MODEL_NAME = 'qwen/qwen-2.5-72b-instruct:free'  # More reliable model

# MODEL_NAMES = [
#     # === PRIMARY EVALUATION MODELS (6 models) ===
#     'meta-llama/llama-3.3-70b-instruct:free',  # 65k context, most reliable
#     'deepseek/deepseek-chat-v3-0324:free',  # 32k context, proven medical reasoning
#     'qwen/qwen3-235b-a22b-07-25:free',  # 262k context, largest context
#     'qwen/qwen-2.5-72b-instruct:free',  # 32k context, Qwen2.5 comparison
#     'google/gemma-3-27b-it:free',  # 96k context, Gemma baseline
#     'mistralai/mistral-small-3.2-24b-instruct:free',  # 128k context, Mistral 24B
    
#     # === FINE-TUNING MODELS ( models) ===
#     #'mistralai/mistral-7b-instruct:free',  # 7B params, easy to fine-tune
#     #'google/gemma-3-4b-it:free',  # 4B params, very easy to fine-tune
# ]
class MedicalPatientSimulator:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        """Load NHS dataset and personas"""
        try:
            # Load NHS dataset - try prioritized version first, fallback to exact
            base_dir = os.path.dirname(os.path.abspath(__file__))
            nhs_path = os.path.join(base_dir, 'disease_to_symptom_sentences_prioritized.json')
            
            if not os.path.exists(nhs_path):
                nhs_path = os.path.join(base_dir, 'disease_to_symptom_sentences_exact.json')
                if not os.path.exists(nhs_path):
                    raise FileNotFoundError(f"No symptom dataset found in {base_dir}")
            
            with open(nhs_path, 'r', encoding='utf-8') as f:
                self.nhs_data = json.load(f)
            
            # Handle both old and new format
            if isinstance(next(iter(self.nhs_data.values())), dict):
                # New prioritized format
                print(f"Loaded {len(self.nhs_data)} diseases from prioritized dataset")
                self.use_prioritized_symptoms = True
            else:
                # Old format
                print(f"Loaded {len(self.nhs_data)} diseases from exact dataset")
                self.use_prioritized_symptoms = False
                
            self.disease_names = list(self.nhs_data.keys())
            
            # Load personas
            personas_path = os.path.join(base_dir, 'personas.json')
            with open(personas_path, 'r', encoding='utf-8') as f:
                self.personas_data = json.load(f)
            print(f"Loaded {len(self.personas_data['personalities'])} personality types from {personas_path}")
        except FileNotFoundError as e:
            print(f"Error loading data files: {e}")
            self.nhs_data = {}
            self.personas_data = None

    def generate_patient(self):
        """Randomly select a case and build patient data"""
        if not self.nhs_data:
            return None
        disease = random.choice(list(self.nhs_data.keys()))
        symptoms = self.nhs_data[disease]
        return {
            'condition_name': disease,
            'symptoms': symptoms,
        }
    
    def generate_random_patient(self):
        """Generate a random patient with NHS condition and personality"""
        if not self.nhs_data or not self.personas_data:
            return self._fallback_patient()
        
        # Select random condition from NHS dataset
        disease = random.choice(list(self.nhs_data.keys()))
        
        # Handle both old and new symptom formats
        if hasattr(self, 'use_prioritized_symptoms') and self.use_prioritized_symptoms:
            # New prioritized format
            disease_data = self.nhs_data[disease]
            symptoms = disease_data['primary_symptoms'] + disease_data['secondary_symptoms']
            primary_symptoms = disease_data['primary_symptoms']
            secondary_symptoms = disease_data['secondary_symptoms']
        else:
            # Old format
            symptoms = self.nhs_data[disease]
            primary_symptoms = symptoms[:min(3, len(symptoms))]
            secondary_symptoms = symptoms[min(3, len(symptoms)):] if len(symptoms) > 3 else []
        
        # Select random personality
        personality = random.choice(self.personas_data['personalities'])
        
        # Generate demographic details
        demographics = self._generate_demographics(personality)
        
        # Build patient data
        patient_data = {
            'name': demographics['name'],
            'age': demographics['age'],
            'gender': demographics['gender'],
            'occupation': demographics['occupation'],
            'personality_type': personality['id'],
            'condition_name': disease,
            'condition_url': '',  # No URL for Symbipredict data
            'symptoms': symptoms,
            'primary_symptoms': primary_symptoms,
            'secondary_symptoms': secondary_symptoms,
            'treatments': [],  # No treatments in Symbipredict data
            'personality_traits': personality['personality_traits'],
            'behavior_notes': personality['behavior_notes'],
            'communication_style': personality['communication_style'],
            'diagnosis_given': False  # Flag to track if correct diagnosis was given
        }
        
        # Generate the prompt template
        patient_data['prompt_template'] = build_prompt_template(patient_data, disease, symptoms)
        
        return patient_data
    
    def _generate_demographics(self, personality):
        """Generate demographics from fixed persona data"""
        # Use fixed name, age, and occupation from persona
        name = personality['name']
        
        # Generate gender based on name
        male_names = ['Robert', 'James', 'Michael', 'Frank', 'George', 'Jake', 'Tyler']
        gender = 'Male' if any(male_name in name for male_name in male_names) else 'Female'
        
        return {
            'name': name,
            'age': personality['age'],
            'gender': gender,
            'occupation': personality['occupation']
        }
    
    def generate_mcq_questions(self, patient_data, num_questions=3):
        """Generate MCQ questions based on the patient's condition"""
        questions = []
        
        # Get all available conditions for distractors from Symbipredict dataset
        all_conditions = [disease for disease in self.disease_names if disease != patient_data['condition_name']]
        
        # Question 1: What is the most likely diagnosis?
        correct_answer = patient_data['condition_name']
        distractors = random.sample(all_conditions, min(3, len(all_conditions)))
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        questions.append({
            'question': f"Based on the patient's symptoms ({', '.join(patient_data['symptoms'][:3])}), what is the most likely diagnosis?",
            'options': options,
            'correct_answer': correct_answer,
            'explanation': f"The patient presents with symptoms typical of {correct_answer}."
        })
        
        # Question 2: Which symptom is most characteristic?
        if patient_data.get('primary_symptoms'):
            # Use primary symptoms for this question
            correct_symptom = random.choice(patient_data['primary_symptoms'])
            # Generate distractors from other conditions 
            all_symptoms = []
            for disease, symptoms in self.nhs_data.items():
                if disease != patient_data['condition_name']:
                    if hasattr(self, 'use_prioritized_symptoms') and self.use_prioritized_symptoms:
                        # New format
                        disease_data = symptoms
                        if isinstance(disease_data, dict):
                            all_symptoms.extend(disease_data.get('primary_symptoms', []))
                        else:
                            all_symptoms.extend(symptoms[:min(3, len(symptoms))])
                    else:
                        # Old format
                        all_symptoms.extend(symptoms[:min(3, len(symptoms))])
            
            distractors = random.sample(all_symptoms, min(3, len(all_symptoms))) if all_symptoms else ["Headache", "Fatigue", "Nausea"]
            options = [correct_symptom] + distractors
            random.shuffle(options)
            
            questions.append({
                'question': f"Which symptom is most characteristic of {patient_data['condition_name']}?",
                'options': options,
                'correct_answer': correct_symptom,
                'explanation': f"{correct_symptom} is a key symptom of {patient_data['condition_name']}."
            })
        
        # Question 3: What is the appropriate next step?
        next_steps = [
            "Order blood tests",
            "Prescribe antibiotics",
            "Refer to specialist",
            "Recommend lifestyle changes",
            "Schedule follow-up appointment"
        ]
        
        # Determine appropriate next step based on condition
        if "infection" in patient_data['condition_name'].lower():
            correct_step = "Prescribe antibiotics"
        elif "chronic" in patient_data['condition_name'].lower():
            correct_step = "Refer to specialist"
        else:
            correct_step = "Order blood tests"
        
        distractors = [step for step in next_steps if step != correct_step]
        options = [correct_step] + random.sample(distractors, 3)
        random.shuffle(options)
        
        questions.append({
            'question': f"What is the most appropriate next step for managing {patient_data['condition_name']}?",
            'options': options,
            'correct_answer': correct_step,
            'explanation': f"For {patient_data['condition_name']}, {correct_step.lower()} is the recommended approach."
        })
        
        return questions
    
    def _fallback_patient(self):
        """Fallback patient if data files are missing"""
        return {
            'name': 'Test Patient',
            'age': 35,
            'gender': 'Female',
            'occupation': 'Office worker',
            'personality_type': 'anxious_professional',
            'condition_name': 'Asthma',
            'condition_url': 'https://www.nhs.uk/conditions/asthma/',
            'symptoms': ['wheezing', 'coughing', 'shortness of breath'],
            'treatments': ['inhaler'],
            'personality_traits': 'Anxious and concerned about health',
            'behavior_notes': 'Asks many questions',
            'communication_style': 'Formal but worried',
            'prompt_template': 'You are a concerned patient with asthma symptoms.',
            'diagnosis_given': False
        }

# Initialize simulator
simulator = MedicalPatientSimulator()

def get_patient_response(patient_data, conversation_history, user_message, model_name=MODEL_NAME):
    """Generate patient response using OpenAI API with enhanced responses. Returns (response, is_error)."""
    
    # Retry configuration
    RESPONSE_RETRY_LIMIT = 3
    RESPONSE_RETRY_DELAY = 5  # seconds
    
    # Use the provided model_name if given, otherwise default
    model = model_name if model_name is not None else MODEL_NAME
    
    # Check if this is a new patient session (reset diagnosis flag)
    if 'diagnosis_given' not in patient_data:
        patient_data['diagnosis_given'] = False
    
    for retry in range(RESPONSE_RETRY_LIMIT):
        try:
            # Check if this is a diagnosis - look for exact condition name
            condition_name_lower = patient_data['condition_name'].lower()
            user_message_lower = user_message.lower()
            
            # Check for exact condition name or close match (case-insensitive)
            is_correct_diagnosis = (
                condition_name_lower in user_message_lower or
                any(word in user_message_lower for word in condition_name_lower.split()) or
                any(symptom in user_message_lower for symptom in patient_data['symptoms'])
            )
            
            # If correct diagnosis is given, set the flag
            if is_correct_diagnosis:
                patient_data['diagnosis_given'] = True
            
            # Check if this looks like a diagnosis attempt - more specific keywords
            diagnosis_keywords = [
                "i think you have", "diagnosis is", "you have", 
                "it appears to be", "this looks like", "based on your symptoms",
                "this is", "you've got", "it's", "that's"
            ]
            is_diagnosis_attempt = any(keyword in user_message_lower for keyword in diagnosis_keywords)
            
            # Build conversation context using new prompt template
            prompt_template = build_prompt_template(patient_data, patient_data['condition_name'], patient_data['symptoms'])
            messages = [
                {"role": "system", "content": prompt_template},
            ]
            
            # Add conversation history (limit to last 5 exchanges for context)
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            for entry in recent_history:
                messages.append({"role": "user", "content": f"Doctor: {entry['doctor']}"})
                messages.append({"role": "assistant", "content": entry['patient']})
            
            # Add current message
            messages.append({"role": "user", "content": f"Doctor: {user_message}"})
            
            # Add diagnosis context if this is a diagnosis attempt
            if is_diagnosis_attempt:
                if is_correct_diagnosis:
                    messages.append({
                        "role": "system", 
                        "content": f"The doctor just correctly identified your condition as '{patient_data['condition_name']}'. Thank them naturally and end the conversation. Use simple thank you phrases like 'Thank you doctor', 'Thanks doc', 'Thankyou doctor', or 'Thankyou doctor for helping me'."
                    })
                else:
                    messages.append({
                        "role": "system", 
                        "content": f"The doctor just gave an incorrect diagnosis. Help them understand better by describing your symptoms more clearly."
                    })
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=250,  # Increased to 250 tokens for word limit testing
                temperature=0.8  # Slightly higher for more natural variation
            )
            content = response.choices[0].message.content.strip() if response.choices[0].message.content else "I'm not sure how to respond to that."
            return content, False
            
        except Exception as e:
            # Better error handling for model issues
            error_str = str(e)
            if "503" in error_str or "No instances available" in error_str:
                error_msg = f"Model '{model}' is currently unavailable on OpenRouter. Please try a different model."
            elif "idk how to respond" in error_str.lower():
                error_msg = f"Model '{model}' is not responding properly. This may be a compatibility issue."
            else:
                error_msg = f"API Error with model '{model}': {error_str}"
            
            print(f"Model error (attempt {retry + 1}/{RESPONSE_RETRY_LIMIT}): {error_msg}")
            
            # If this is the last retry, return the error
            if retry == RESPONSE_RETRY_LIMIT - 1:
                return error_msg, True
            
            # Otherwise, wait and retry
            print(f"[Retrying LLM] Attempt {retry + 1}/{RESPONSE_RETRY_LIMIT} after {RESPONSE_RETRY_DELAY}s...")
            time.sleep(RESPONSE_RETRY_DELAY)

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard to monitor logs and feedback"""
    return render_template('admin_dashboard.html')

@app.route('/disease_list')
def disease_list():
    """Show list of available diseases for users"""
    # Create a list of diseases with their symptoms
    diseases_with_symptoms = []
    for disease_name in simulator.disease_names:
        disease_data = simulator.nhs_data[disease_name]
        
        # Handle both old and new symptom formats
        if hasattr(simulator, 'use_prioritized_symptoms') and simulator.use_prioritized_symptoms:
            # New prioritized format
            symptoms = disease_data['primary_symptoms'] + disease_data['secondary_symptoms']
        else:
            # Old format
            symptoms = disease_data if isinstance(disease_data, list) else []
        
        diseases_with_symptoms.append({
            'name': disease_name,
            'symptoms': symptoms
        })
    
    return render_template('disease_list.html', diseases=diseases_with_symptoms)

@app.route('/about')
def about():
    """About page for the medical patient simulator"""
    return render_template('about.html')

@app.route('/')
def index():
    """Main page - generate a new random patient"""
    return render_template('index.html')

@app.route('/generate_patient')
def generate_patient():
    """Generate a new random patient and redirect to chat"""
    patient_data = simulator.generate_random_patient()
    
    # Ensure diagnosis flag is reset for new patient
    patient_data['diagnosis_given'] = False
    
    # Store patient data in session
    session['patient_data'] = patient_data
    session['conversation_history'] = []
    session['conversation_id'] = str(uuid.uuid4())
    
    return jsonify({
        'success': True,
        'redirect': '/chat'
    })

@app.route('/chat')
def chat():
    """Chat interface - Pure text-based chat"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return redirect('/')
    
    return render_template('chat.html', patient_data=patient_data)

@app.route('/chat_2d')
def chat_2d():
    """2D animated character interface with action mapping"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return redirect('/')
    
    return render_template('chat_2d.html', patient_data=patient_data)

@app.route('/animation_test')
def animation_test():
    """2D animation testing interface (for debugging)"""
    return render_template('chat_2d_animation_test.html')

@app.route('/chat_3d')
def chat_3d():
    """Chat interface with comprehensive 3D Three.js character"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return redirect('/')
    
    return render_template('chat_3d_comprehensive.html', patient_data=patient_data)

@app.route('/chat_3d_avatar')
def chat_3d_avatar():
    """Advanced 3D avatar with detailed human model and animations"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return redirect('/')
    
    return render_template('chat_3d_avatar.html', patient_data=patient_data)

@app.route('/chat_3d_procedural')
def chat_3d_procedural():
    """3D procedural avatar interface"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return redirect('/')
    
    return render_template('chat_3d_procedural.html', patient_data=patient_data)

def check_if_should_end_chat(patient_response, patient_data=None):
    """Check if patient response indicates the conversation should end"""
    response_lower = patient_response.lower()
    
    # Enhanced thank you patterns with flexible matching (case-insensitive)
    thank_you_patterns = [
        'thank you doctor',
        'thank you doc', 
        'thanks doctor',
        'thanks doc',
        'thankyou doctor',
        'thankyou doc',
        'thankyou doctor for helping me',
        'thanks doc, you have been a great help',
        'thank you for the diagnosis',
        'thanks for the diagnosis',
        'thank you for helping',
        'thanks for helping',
        'thank you for your help',
        'thanks for your help',
        'thank you so much',
        'thanks so much'
    ]
    
    # Check for flexible thank you patterns (allowing commas, no spaces, and variations)
    flexible_patterns = [
        r'thank\s*you\s*,?\s*doctor',
        r'thanks\s*,?\s*doc',
        r'thank\s*you\s*,?\s*doc',
        r'thanks\s*,?\s*doctor',
        r'thankyou\s*,?\s*doctor',
        r'thankyou\s*,?\s*doc',
        r'thank\s*you\s*,?\s*doctor',
        r'thanks\s*,?\s*doctor'
    ]
    
    # Check if any exact thank you pattern is found
    for pattern in thank_you_patterns:
        if pattern in response_lower:
            return True
    
    # Check for flexible patterns using regex-like matching
    import re
    for pattern in flexible_patterns:
        if re.search(pattern, response_lower, re.IGNORECASE):
            return True
    
    # Additional flexible matching for common variations
    additional_patterns = [
        'thankyou doctor',
        'thankyou doc',
        'thank you, doctor',
        'thank you, doc',
        'thanks, doctor',
        'thanks, doc',
        'thankyou, doctor',
        'thankyou, doc'
    ]
    
    for pattern in additional_patterns:
        if pattern in response_lower:
            return True
    
    # Check for goodbye/farewell patterns that might also indicate end
    farewell_patterns = [
        'goodbye doctor',
        'bye doctor',
        'see you later',
        'have a good day',
        'take care'
    ]
    
    for pattern in farewell_patterns:
        if pattern in response_lower:
            return True
    
    return False

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handle chat messages and generate patient responses"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get patient data from session
        patient_data = session.get('patient_data')
        if not patient_data:
            return jsonify({'error': 'No patient data found. Please generate a patient first.'}), 400
        
        # Get conversation history from session
        conversation_history = session.get('conversation_history', [])
        
        # Generate patient response using OpenAI
        patient_response, is_error = get_patient_response(
            patient_data, conversation_history, user_message
        )
        
        # Detect actions only from the patient's response (per requirement)
        patient_action_result = process_patient_message(patient_response)
        action_result = {
            'actions': patient_action_result.get('actions', []),
            'execution_plan': patient_action_result.get('execution_plan', '')
        }
        
        # Log the conversation
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'doctor': user_message,
            'patient': patient_response,
            'symptoms_revealed': action_result.get('actions', []),
            'diagnosis_attempts': 0,
            'session_end': False
        }
        
        conversation_history.append(conversation_entry)
        session['conversation_history'] = conversation_history
        
        # Log to file
        conversation_id = session.get('conversation_id', 'unknown')
        log_conversation(conversation_id, patient_data, conversation_entry)
        
        # Check if patient response indicates end of conversation (thank you messages)
        # Only end if diagnosis was given AND thank you is detected
        should_end = False
        if patient_data.get('diagnosis_given', False):
            should_end = check_if_should_end_chat(patient_response, patient_data)
        
        return jsonify({
            'response': patient_response,
            'detected_actions': action_result.get('actions', []),
            'execution_plan': action_result.get('execution_plan', ''),
            'should_end_chat': should_end
        })
        
    except Exception as e:
        print(f"Error in send_message: {e}")
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq():
    """Generate MCQ questions for the current patient"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return jsonify({'error': 'No patient data found'})
    
    questions = simulator.generate_mcq_questions(patient_data, num_questions=3)
    
    return jsonify({
        'questions': questions,
        'patient_condition': patient_data['condition_name'],
        'patient_symptoms': patient_data['symptoms']
    })

@app.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    """Reset the current conversation"""
    session['conversation_history'] = []
    session['conversation_id'] = str(uuid.uuid4())
    
    # Reset diagnosis flag when conversation is reset
    if 'patient_data' in session:
        session['patient_data']['diagnosis_given'] = False
    
    return jsonify({'success': True})

@app.route('/new_patient', methods=['POST'])
def new_patient():
    """Generate a new patient"""
    patient_data = simulator.generate_random_patient()
    # Ensure diagnosis flag is reset for new patient
    patient_data['diagnosis_given'] = False
    session['patient_data'] = patient_data
    session['conversation_history'] = []
    session['conversation_id'] = str(uuid.uuid4())
    
    # No need to clear action queue anymore - actions are processed per message
    
    return jsonify({
        'success': True,
        'patient_data': patient_data
    })

@app.route('/submit_diagnosis', methods=['POST'])
def submit_diagnosis():
    """Check the submitted diagnosis against the patient's true condition"""
    data = request.get_json()
    diagnosis = data.get('diagnosis', '').strip().lower()
    patient_data = session.get('patient_data')
    if not patient_data:
        return jsonify({'error': 'No patient data found', 'correct': False})
    true_condition = patient_data['condition_name'].strip().lower()
    # Robust match: allow for minor typos (Levenshtein), but for now, simple substring/case-insensitive
    is_correct = (diagnosis == true_condition) or (true_condition in diagnosis) or (diagnosis in true_condition)
    return jsonify({'correct': is_correct, 'should_end_chat': is_correct})

@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Return the correct diagnosis and one random distractor as a hint"""
    patient_data = session.get('patient_data')
    if not patient_data:
        return jsonify({'hint': 'No patient data found.'})
    true_condition = patient_data['condition_name']
    # Get a random distractor from the CSV-based disease list
    all_conditions = [d for d in simulator.disease_names if d != true_condition]
    distractor = random.choice(all_conditions) if all_conditions else 'Migraine'
    hint = f"Possible diagnoses: {true_condition}, {distractor}"
    return jsonify({'hint': hint})

@app.route('/test_action_mapper', methods=['POST'])
def test_action_mapper():
    """Test the action mapper with a sample message"""
    data = request.get_json()
    test_message = data.get('message', '')
    
    if not test_message:
        return jsonify({'error': 'No message provided'})
    
    detected_actions = process_patient_message(test_message)
    
    return jsonify({
        'message': test_message,
        'detected_actions': detected_actions['actions'],
        'execution_plan': detected_actions['execution_plan']
    })

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback form submissions"""
    try:
        data = request.get_json()
        
        # Extract feedback data
        feedback_data = {
            'timestamp': datetime.now().isoformat(),
            'authenticity_rating': data.get('authenticity_rating'),
            'educational_value_rating': data.get('educational_value_rating'),
            'interaction_quality_rating': data.get('interaction_quality_rating'),
            'communication_consistency_rating': data.get('communication_consistency_rating'),
            'symptom_realism_rating': data.get('symptom_realism_rating'),
            'additional_comments': data.get('additional_comments', ''),
            'patient_data': session.get('patient_data', {}),
            'conversation_id': session.get('conversation_id', 'unknown'),
            'session_id': session.get('session_id', 'unknown')
        }
        
        # Log feedback to file
        log_feedback(feedback_data)
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

def log_feedback(feedback_data):
    """Log feedback data for analysis"""
    # Save to feedback log file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    feedback_dir = os.path.join(base_dir, 'feedback_logs')
    os.makedirs(feedback_dir, exist_ok=True)
    feedback_file = os.path.join(feedback_dir, f"feedback_{datetime.now().strftime('%Y%m%d')}.jsonl")
    
    with open(feedback_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(feedback_data) + '\n')


def log_conversation(conversation_id, patient_data, entry):
    """Log conversation for analysis"""
    log_entry = {
        'conversation_id': conversation_id,
        'patient_name': patient_data['name'],
        'condition': patient_data['condition_name'],
        'personality_type': patient_data['personality_type'],
        'timestamp': entry['timestamp'],
        'doctor_message': entry['doctor'],
        'patient_response': entry['patient'],
        'model_name': MODEL_NAME,
        'symptoms_revealed': entry['symptoms_revealed'],
        'diagnosis_attempts': entry['diagnosis_attempts'],
        'session_end': entry['session_end']
    }
    
    # Save to log file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"conversations_{datetime.now().strftime('%Y%m%d')}.jsonl")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    """Generate audio for a patient message using ElevenLabs TTS"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        patient_data = session.get('patient_data')
        
        if not message or not patient_data:
            return jsonify({'error': 'Missing message or patient data'}), 400
        
        # Get ElevenLabs API key from environment
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            return jsonify({'error': 'ElevenLabs API key not configured'}), 500
        
        # Build the voice prompt based on patient personality and symptoms
        voice_prompt = build_voice_prompt(message, patient_data)
        
        # Clean the message text for TTS (remove special characters that might be read aloud)
        cleaned_message = clean_text_for_tts(message)
        
        # ElevenLabs API call
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Rachel voice (medical professional)
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        payload = {
            "text": cleaned_message,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        # Add voice prompt for personality/emotion
        if voice_prompt:
            payload["text"] = f"[{voice_prompt}] {cleaned_message}"
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            # Save audio file temporarily
            audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'audio')
            os.makedirs(audio_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_filename = f"patient_audio_{timestamp}.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            # Return audio file URL
            audio_url = f"/static/audio/{audio_filename}"
            
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'message': 'Audio generated successfully'
            })
        else:
            return jsonify({
                'error': f'ElevenLabs API error: {response.status_code}',
                'details': response.text
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error generating audio: {str(e)}'}), 500

def clean_text_for_tts(text):
    """Clean text for TTS by removing special characters that might be read aloud"""
    import re
    
    # Remove or replace special characters that TTS might read literally
    cleaned = text
    
    # Remove asterisks, backslashes, and other special characters
    cleaned = re.sub(r'[\*\\\/\[\]\(\)\{\}\|\-\+\=\&\^\%\$\#\@\!\?\.\,]', ' ', cleaned)
    
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove leading/trailing spaces
    cleaned = cleaned.strip()
    
    # If text becomes empty, return a fallback
    if not cleaned:
        cleaned = "Patient message"
    
    return cleaned

def build_voice_prompt(message, patient_data):
    """Build a voice prompt that captures patient personality and emotional state"""
    try:
        # Extract personality traits
        personality_type = patient_data.get('personality_type', 'neutral')
        communication_style = patient_data.get('communication_style', 'neutral')
        personality_traits = patient_data.get('personality_traits', '')
        
        # Analyze message content for emotional cues
        emotional_keywords = {
            'pain': 'worried, concerned',
            'hurt': 'distressed, in discomfort',
            'scared': 'anxious, fearful',
            'worried': 'anxious, concerned',
            'fine': 'calm, reassured',
            'better': 'relieved, optimistic',
            'terrible': 'distressed, in pain',
            'okay': 'neutral, calm'
        }
        
        # Detect emotional state from message
        detected_emotion = 'neutral'
        message_lower = message.lower()
        for keyword, emotion in emotional_keywords.items():
            if keyword in message_lower:
                detected_emotion = emotion
                break
        
        # Build personality prompt
        personality_prompt = ""
        if personality_type == 'anxious':
            personality_prompt = "speaking anxiously, with worry in voice"
        elif personality_type == 'confident':
            personality_prompt = "speaking confidently, clear and assured"
        elif personality_type == 'reserved':
            personality_prompt = "speaking quietly, reserved manner"
        elif personality_type == 'talkative':
            personality_prompt = "speaking enthusiastically, engaging tone"
        
        # Add communication style
        if communication_style == 'formal':
            personality_prompt += ", formal speech pattern"
        elif communication_style == 'casual':
            personality_prompt += ", casual, friendly tone"
        elif communication_style == 'technical':
            personality_prompt += ", precise, medical terminology"
        
        # Combine everything
        final_prompt = f"Patient with {personality_prompt}, currently feeling {detected_emotion}"
        
        return final_prompt
        
    except Exception as e:
        print(f"Error building voice prompt: {e}")
        return "Patient speaking naturally"

@app.route('/download_logs/<filename>')
def download_logs(filename):
    """Download a specific conversation log file"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')
        
        if not os.path.exists(logs_dir):
            return jsonify({'error': 'No logs directory found'}), 404
        
        # Validate filename to prevent directory traversal
        if not filename.startswith('conversations_') or not filename.endswith('.jsonl'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        log_path = os.path.join(logs_dir, filename)
        
        if not os.path.exists(log_path):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(log_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'Failed to download logs: {str(e)}'}), 500

@app.route('/download_feedback/<filename>')
def download_feedback(filename):
    """Download a specific feedback log file"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_dir = os.path.join(base_dir, 'feedback_logs')
        
        if not os.path.exists(feedback_dir):
            return jsonify({'error': 'No feedback directory found'}), 400
        
        # Validate filename to prevent directory traversal
        if not filename.startswith('feedback_') or not filename.endswith('.jsonl'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        feedback_path = os.path.join(feedback_dir, filename)
        
        if not os.path.exists(feedback_path):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(feedback_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'Failed to download feedback: {str(e)}'}), 500

# Keep the old routes for backward compatibility but mark them as deprecated
@app.route('/download_logs')
def download_logs_legacy():
    """Download the most recent conversation log file (deprecated)"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')
        
        if not os.path.exists(logs_dir):
            return jsonify({'error': 'No logs directory found'}), 404
        
        # Get the most recent log file
        log_files = [f for f in os.listdir(logs_dir) if f.startswith('conversations_') and f.endswith('.jsonl')]
        if not log_files:
            return jsonify({'error': 'No log files found'}), 404
        
        # Sort by date and get the most recent
        log_files.sort(reverse=True)
        latest_log = log_files[0]
        log_path = os.path.join(logs_dir, latest_log)
        
        from flask import send_file
        return send_file(log_path, as_attachment=True, download_name=latest_log)
        
    except Exception as e:
        return jsonify({'error': f'Failed to download logs: {str(e)}'}), 500

@app.route('/download_feedback')
def download_feedback_legacy():
    """Download the most recent feedback log file (deprecated)"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_dir = os.path.join(base_dir, 'feedback_logs')
        
        if not os.path.exists(feedback_dir):
            return jsonify({'error': 'No feedback directory found'}), 400
        
        # Get the most recent feedback file
        feedback_files = [f for f in os.listdir(feedback_dir) if f.startswith('feedback_') and f.endswith('.jsonl')]
        if not feedback_files:
            return jsonify({'error': 'No feedback files found'}), 400
        
        # Sort by date and get the most recent
        feedback_files.sort(reverse=True)
        latest_feedback = feedback_files[0]
        feedback_path = os.path.join(feedback_dir, latest_feedback)
        
        from flask import send_file
        return send_file(feedback_path, as_attachment=True, download_name=latest_feedback)
        
    except Exception as e:
        return jsonify({'error': f'Failed to download feedback: {str(e)}'}), 500

@app.route('/view_logs')
def view_logs():
    """View logs in browser (for debugging)"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')
        
        if not os.path.exists(logs_dir):
            return jsonify({'error': 'No logs directory found'}), 404
        
        # Get all log files
        log_files = [f for f in os.listdir(logs_dir) if f.startswith('conversations_') and f.endswith('.jsonl')]
        log_files.sort(reverse=True)
        
        logs_data = []
        for log_file in log_files[:5]:  # Show last 5 log files
            log_path = os.path.join(logs_dir, log_file)
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    logs_data.append({
                        'filename': log_file,
                        'line_count': len(lines),
                        'last_modified': os.path.getmtime(log_path)
                    })
            except Exception as e:
                logs_data.append({
                    'filename': log_file,
                    'error': str(e)
                })
        
        return jsonify({
            'logs_directory': logs_dir,
            'log_files': logs_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to view logs: {str(e)}'}), 500

@app.route('/view_feedback')
def view_feedback():
    """View feedback in browser (for debugging)"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_dir = os.path.join(base_dir, 'feedback_logs')
        
        if not os.path.exists(feedback_dir):
            return jsonify({'error': 'No feedback directory found'}), 404
        
        # Get all feedback files
        feedback_files = [f for f in os.listdir(feedback_dir) if f.startswith('feedback_') and f.endswith('.jsonl')]
        feedback_files.sort(reverse=True)
        
        feedback_data = []
        for feedback_file in feedback_files[:5]:  # Show last 5 feedback files
            feedback_path = os.path.join(feedback_dir, feedback_file)
            try:
                with open(feedback_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    feedback_data.append({
                        'filename': feedback_file,
                        'line_count': len(lines),
                        'last_modified': os.path.getmtime(feedback_path)
                    })
            except Exception as e:
                feedback_data.append({
                    'filename': feedback_file,
                    'error': str(e)
                })
        
        return jsonify({
            'feedback_directory': feedback_dir,
            'feedback_files': feedback_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to view feedback: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)