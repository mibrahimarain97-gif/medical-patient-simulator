# Admin Dashboard for Medical Patient Simulator

This document explains how to monitor and access your application logs and feedback data when deployed on Render.

## 🚀 New Admin Features

### 1. Admin Dashboard
- **URL**: `/admin` (e.g., `https://your-app.onrender.com/admin`)
- **Purpose**: Visual interface to monitor logs and feedback
- **Features**: 
  - Real-time statistics
  - File browsing
  - Download capabilities
  - System information

### 2. API Endpoints for Monitoring

#### View Logs
- **GET** `/view_logs`
- **Purpose**: Get information about conversation log files
- **Returns**: JSON with file details, line counts, and timestamps

#### Download Logs
- **GET** `/download_logs`
- **Purpose**: Download the most recent conversation log file
- **Returns**: File download (JSONL format)

#### View Feedback
- **GET** `/view_feedback`
- **Purpose**: Get information about feedback submission files
- **Returns**: JSON with file details, submission counts, and timestamps

#### Download Feedback
- **GET** `/download_feedback`
- **Purpose**: Download the most recent feedback log file
- **Returns**: File download (JSONL format)

## 📁 File Structure on Render

Your app automatically creates these directories:

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

## 🔍 How to Monitor Your App

### Option 1: Admin Dashboard (Recommended)
1. Visit `https://your-app.onrender.com/admin`
2. Click "🔄 Refresh Data" to update statistics
3. View real-time file information
4. Download files directly from the interface

### Option 2: Direct API Calls
```bash
# View logs info
curl https://your-app.onrender.com/view_logs

# Download latest logs
curl -O https://your-app.onrender.com/download_logs

# View feedback info
curl https://your-app.onrender.com/view_feedback

# Download latest feedback
curl -O https://your-app.onrender.com/download_feedback
```

### Option 3: Browser
- Navigate directly to the URLs in your browser
- `/view_logs` - See log file information
- `/view_feedback` - See feedback file information

## 📊 Understanding the Data

### Conversation Logs (JSONL format)
Each line is a JSON object containing:
```json
{
  "conversation_id": "uuid",
  "patient_name": "John Doe",
  "condition": "Hypertension",
  "personality_type": "Anxious",
  "timestamp": "2025-01-01T12:00:00",
  "doctor_message": "What brings you in today?",
  "patient_response": "I've been having headaches...",
  "model_name": "mistralai/mistral-small-3.2-24b-instruct:free",
  "symptoms_revealed": ["headache", "dizziness"],
  "diagnosis_attempts": 2,
  "session_end": false
}
```

### Feedback Logs (JSONL format)
Each line is a JSON object containing:
```json
{
  "timestamp": "2025-01-01T12:00:00",
  "authenticity_rating": 4,
  "educational_value_rating": 5,
  "interaction_quality_rating": 4,
  "communication_consistency_rating": 4,
  "symptom_realism_rating": 5,
  "additional_comments": "Great simulation!",
  "patient_data": {...},
  "conversation_id": "uuid",
  "session_id": "uuid"
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **"No logs directory found"**
   - The app hasn't been used yet
   - No conversations have been logged
   - Check if the app is running properly

2. **"No log files found"**
   - Files exist but are empty
   - Check file permissions on Render
   - Verify the app is writing to the correct directories

3. **Download fails**
   - File might be too large for Render's free tier
   - Check Render's file size limits
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

## 🆘 Getting Help

If you encounter issues:
1. Check the admin dashboard for error messages
2. Verify your app is running on Render
3. Check Render's service logs
4. Ensure all required environment variables are set
5. Verify file permissions and directory structure

---

**Note**: This admin system is designed for development and monitoring purposes. For production use, consider implementing proper authentication and access controls.
