# Medical Patient Simulator

An AI-powered medical training application that simulates patient interactions for healthcare professionals and medical students.

## 🚀 Features

- **Interactive Patient Simulation**: Chat with AI-generated patients presenting various medical conditions
- **Multiple Interface Options**: 2D, 3D, and procedural chat interfaces
- **Medical Case Generation**: Random patient cases based on NHS symptom database
- **Personality Variations**: Different patient personalities and communication styles
- **MCQ Generation**: Automatic quiz questions based on patient cases
- **Text-to-Speech**: Audio generation for patient responses
- **Feedback System**: Collect and analyze user feedback
- **Conversation Logging**: Track and review training sessions
- **Admin Dashboard**: Monitor logs, feedback, and system statistics

## 🏗️ Tech Stack

- **Backend**: Flask (Python)
- **AI Integration**: OpenRouter API (Mistral, Llama, Qwen models)
- **Frontend**: HTML, CSS, JavaScript, Three.js for 3D
- **Text-to-Speech**: ElevenLabs API
- **Data**: NHS symptom database, custom personas

## 🚀 Quick Start

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
   ```
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

## 🔑 API Keys Required

- **OpenRouter API Key**: For AI patient responses
- **ElevenLabs API Key**: For text-to-speech functionality

## 📁 Project Structure

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
├── static/                         # Static assets
│   ├── avatars/                   # Patient avatar definitions
│   ├── audio/                     # Generated audio files
│   └── vendor/                    # Third-party libraries
├── logs/                           # Conversation logs
├── feedback_logs/                  # User feedback data
└── data/                           # Medical data files
```

## 💻 Usage

1. **Generate a Patient**: Click "Generate New Patient" to create a random medical case
2. **Start Chatting**: Interact with the patient through the chat interface
3. **Ask Questions**: Use natural language to gather patient history and symptoms
4. **Generate MCQs**: Create quiz questions based on the current case
5. **Submit Diagnosis**: Test your diagnostic skills
6. **Get Feedback**: Receive AI-generated feedback on your approach

## 🚀 Deployment

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

## 📊 Admin Dashboard & Monitoring

### Admin Dashboard
- **URL**: `/admin` (e.g., `https://your-app.onrender.com/admin`)
- **Purpose**: Visual interface to monitor logs and feedback
- **Features**: 
  - Real-time statistics
  - File browsing
  - Download capabilities
  - System information

### API Endpoints for Monitoring

#### View Logs
- **GET** `/view_logs` - Get information about conversation log files
- **GET** `/download_logs` - Download the most recent conversation log file

#### View Feedback
- **GET** `/view_feedback` - Get information about feedback submission files
- **GET** `/download_feedback` - Download the most recent feedback log file

### File Structure on Deployment
```
/app/
├── logs/                           # Conversation logs
│   ├── conversations_20250101.jsonl
│   ├── conversations_20250102.jsonl
│   └── ...
├── feedback_logs/                  # Feedback submissions
│   ├── feedback_20250101.jsonl
│   ├── feedback_20250102.jsonl
│   └── ...
└── static/audio/                   # Generated audio files
    ├── patient_audio_20250101_120000.mp3
    └── ...
```

## 🔧 Key Improvements Made

### 1. **Less Rigid Prompts** ✅
- **Before**: Prompts had strict formatting requirements like "**bold** formatting" and rigid "CRITICAL ROLE-PLAYING RULES"
- **After**: Natural, conversational prompts that focus on character and behavior rather than strict formatting
- **Benefit**: LLMs can act more naturally without worrying about specific formatting requirements

### 2. **Symptom Prioritization** ✅
- **Before**: All symptoms were treated equally, making it hard to identify defining characteristics
- **After**: Symptoms are now categorized into:
  - **Primary symptoms**: Most important/defining symptoms for diagnosis
  - **Secondary symptoms**: Supporting symptoms that may occur but aren't defining
- **Benefit**: Patients will emphasize the most important symptoms, making diagnosis easier

### 3. **Improved Persona Clarity** ✅
- **Before**: Personas had bold formatting and complex instructions
- **After**: Clear, focused personality traits that are easier for LLMs to act out
- **Benefit**: More consistent and believable character behavior

### 4. **Better Symptom Dataset** ✅
- **New file**: `disease_to_symptom_sentences_prioritized.json`
- **Structure**: Each condition now has `primary_symptoms` and `secondary_symptoms` arrays
- **Example - Migraine**:
  - Primary: "throbbing pain on one side of head", "zigzag lines/flashing lights"
  - Secondary: "tiredness", "thirst", "mood changes", etc.

### 5. **Enhanced App Logic** ✅
- **Backward compatibility**: System works with both old and new symptom formats
- **Smart symptom handling**: Automatically detects and uses prioritized symptoms when available
- **Improved MCQ generation**: Questions now focus on primary symptoms for better learning

## 📈 Benefits for Medical Training

1. **Better Diagnosis Practice**: Students can now focus on the most important symptoms
2. **More Realistic Patients**: Less rigid prompts lead to more natural patient behavior
3. **Improved Learning**: MCQ questions now focus on defining symptoms rather than random ones
4. **Consistent Experience**: Symptom prioritization ensures key diagnostic features are always present

## 🛠️ Troubleshooting

### Common Issues

1. **"No logs directory found"**
   - The app hasn't been used yet
   - No conversations have been logged
   - Check if the app is running properly

2. **"No log files found"**
   - Files exist but are empty
   - Check file permissions on deployment platform
   - Verify the app is writing to the correct directories

3. **Download fails**
   - File might be too large for free tier limits
   - Check platform's file size limits
   - Try viewing the file info first

### Render Free Tier Limitations

- **File Storage**: Limited but sufficient for logs
- **File Downloads**: May have size restrictions
- **Concurrent Users**: Limited to 1 active user
- **Uptime**: App sleeps after 15 minutes of inactivity

## 🔒 Security Notes

- The admin dashboard is publicly accessible
- Consider adding authentication if needed
- Logs may contain sensitive medical information
- Be careful with data sharing and compliance

## 📈 Monitoring Best Practices

1. **Regular Checks**: Visit `/admin` daily to monitor usage
2. **Download Logs**: Archive logs weekly for analysis
3. **Monitor Growth**: Watch file sizes and line counts
4. **Error Tracking**: Check for failed submissions or errors
5. **Performance**: Monitor response times and user feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NHS symptom database for medical information
- OpenRouter for AI model access
- ElevenLabs for text-to-speech capabilities
- Three.js for 3D graphics support

## 🆘 Support

For questions or issues, please open an issue on GitHub or contact the development team.

## 🔄 Backward Compatibility

The system maintains full backward compatibility with existing symptom datasets while automatically using the improved prioritized version when available.

## 🚀 Future Enhancements

1. **Expand to 50 conditions**: Apply the same prioritization logic to more medical conditions
2. **Dynamic symptom weighting**: Allow symptoms to have different importance levels
3. **Condition-specific prompts**: Customize prompts based on the specific medical condition
4. **Learning analytics**: Track which symptoms students focus on vs. which they miss
