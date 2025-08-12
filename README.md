# Medical Patient Simulator

An AI-powered medical training application that simulates patient interactions for healthcare professionals and medical students.

## Features

- **Interactive Patient Simulation**: Chat with AI-generated patients presenting various medical conditions
- **Multiple Interface Options**: 2D, 3D, and procedural chat interfaces
- **Medical Case Generation**: Random patient cases based on NHS symptom database
- **Personality Variations**: Different patient personalities and communication styles
- **MCQ Generation**: Automatic quiz questions based on patient cases
- **Text-to-Speech**: Audio generation for patient responses
- **Feedback System**: Collect and analyze user feedback
- **Conversation Logging**: Track and review training sessions

## Tech Stack

- **Backend**: Flask (Python)
- **AI Integration**: OpenRouter API (Mistral, Llama, Qwen models)
- **Frontend**: HTML, CSS, JavaScript, Three.js for 3D
- **Text-to-Speech**: ElevenLabs API
- **Data**: NHS symptom database, custom personas

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/medical-patient-simulator.git
   cd medical-patient-simulator/medical-patient-simulator-deploy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   FLASK_SECRET_KEY=your_secret_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:5000`

## API Keys Required

- **OpenRouter API Key**: For AI patient responses
- **ElevenLabs API Key**: For text-to-speech functionality

## Project Structure

```
medical-patient-simulator-deploy/
├── app.py                          # Main Flask application
├── action_mapper.py                # Patient action processing
├── prompts_and_evaluator.py        # AI prompt management
├── requirements.txt                # Python dependencies
├── templates/                      # HTML templates
│   ├── index.html                 # Main landing page
│   ├── chat.html                  # Basic chat interface
│   ├── chat_2d.html              # 2D animated chat
│   ├── chat_3d.html              # 3D chat interface
│   └── chat_3d_procedural.html   # Procedural 3D chat
├── static/                        # Static assets
│   ├── avatars/                   # Patient avatar definitions
│   ├── audio/                     # Generated audio files
│   └── vendor/                    # Third-party libraries
├── logs/                          # Conversation logs
├── feedback_logs/                 # User feedback data
└── data/                          # Medical data files
```

## Usage

1. **Generate a Patient**: Click "Generate New Patient" to create a random medical case
2. **Start Chatting**: Interact with the patient through the chat interface
3. **Ask Questions**: Use natural language to gather patient history and symptoms
4. **Generate MCQs**: Create quiz questions based on the current case
5. **Submit Diagnosis**: Test your diagnostic skills
6. **Get Feedback**: Receive AI-generated feedback on your approach

## Deployment

### Render (Recommended - Free)
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variables in Render dashboard

### Railway
1. Connect GitHub repository to Railway
2. Deploy automatically from git pushes
3. Set environment variables in Railway dashboard

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NHS symptom database for medical information
- OpenRouter for AI model access
- ElevenLabs for text-to-speech capabilities
- Three.js for 3D graphics support

## Support

For questions or issues, please open an issue on GitHub or contact the development team.
