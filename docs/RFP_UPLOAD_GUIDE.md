# 📤 RFP PDF Upload - Quick Guide

## What Was Added

A complete file upload system for RFP documents (PDF and TXT files).

### New Components

1. **`RfpUpload.jsx`** - File upload component with:
   - Drag & drop support
   - File browser
   - PDF and TXT file support
   - Auto title extraction
   - Upload progress
   - Success/error messages

2. **`RfpUpload.css`** - Beautiful styling for the upload interface

### Updated Components

1. **`AgentWorkflow.jsx`** - Now includes:
   - Toggle between upload and RFP list
   - "Upload New RFP" button
   - Auto-refresh after upload

## How to Use

### For Users

1. **Open the application** at http://localhost:3000

2. **Navigate to "Agent Workflow (Live)" tab**

3. **Click "Upload New RFP" button**

4. **Upload your file:**
   - **Drag & drop** PDF or TXT file into the upload zone
   - **OR click "Browse Files"** to select from your computer

5. **Enter RFP title** (auto-filled from filename)

6. **Click "Upload RFP"**

7. **Wait for confirmation** - File will be processed and added to the list

8. **Click "View RFPs"** to see all uploaded RFPs

9. **Select your RFP** to start the agent workflow

### Backend Processing

When you upload a file:

1. **File is saved** to `agentSystem/uploads/` directory
2. **Text is extracted:**
   - **PDF:** Uses PyMuPDF to extract all text
   - **TXT:** Reads file content directly
3. **RFP record created** in database with:
   - Title
   - Extracted content
   - File path
   - Status: "uploaded"
4. **Ready for processing** by agents

## API Endpoint

```http
POST /rfp/upload-file
Content-Type: multipart/form-data

Form Data:
  file: [PDF or TXT file]

Response:
{
  "status": "File uploaded",
  "rfp_id": 1,
  "filename": "project-rfp.pdf",
  "text_length": 2543
}
```

## File Support

### Supported Formats
- ✅ **PDF** (.pdf) - Text extraction via PyMuPDF
- ✅ **TXT** (.txt) - Direct text reading

### Coming Soon
- 📄 DOCX (Word documents)
- 📊 Excel files for pricing
- 🖼️ Image-based PDFs with OCR

## Features

### User Experience
- 🎨 Beautiful drag & drop interface
- 📎 File preview before upload
- ✏️ Editable title field
- ⏱️ Upload progress indicator
- ✅ Success confirmation
- ⚠️ Error handling
- 🔄 Auto-refresh RFP list

### Technical Features
- File validation (type and size)
- Automatic text extraction
- Database persistence
- File system storage
- Error recovery
- CORS enabled

## Testing

### Test with Sample PDF

1. Create a sample PDF with RFP content
2. Upload via the interface
3. Check database:
   ```sql
   SELECT * FROM rfps ORDER BY id DESC LIMIT 1;
   ```
4. Verify file in `agentSystem/uploads/`
5. Start workflow with uploaded RFP

### Test with TXT File

1. Create `sample-rfp.txt` with content:
   ```
   PROJECT: Office Building Paint Tender
   
   Requirements:
   - 1000 liters exterior emulsion
   - 500 liters interior primer
   - Delivery within 30 days
   
   Budget: ₹5,00,000
   ```
2. Upload the file
3. Verify extraction in database
4. Process with agents

## Troubleshooting

### Upload Fails

**Problem:** File upload returns error

**Solutions:**
- Verify backend is running on port 8000
- Check CORS is enabled in `app.py`
- Ensure `uploads/` directory exists
- Check file size (should be < 10MB typically)

### PDF Text Not Extracted

**Problem:** PDF uploads but text is empty

**Solutions:**
- Install PyMuPDF: `pip install PyMuPDF`
- Verify PDF has text (not image-only)
- Check backend logs for errors
- Try converting PDF to TXT first

### File Not in List

**Problem:** Upload succeeds but RFP not visible

**Solutions:**
- Click "View RFPs" to refresh
- Check database: `SELECT * FROM rfps;`
- Restart React app
- Clear browser cache

## File Storage

### Directory Structure
```
agentSystem/
├── uploads/           # Uploaded files stored here
│   ├── project-rfp.pdf
│   ├── tender-doc.pdf
│   └── requirements.txt
└── routers/
    └── rfp.py        # Upload endpoint
```

### Database Storage
```sql
-- RFP Table Structure
id: integer
title: string              -- File name or custom title
content: text              -- Extracted text content
file_path: string          -- Path to original file
status: string             -- uploaded, analyzing, completed
sales_summary: json        -- Agent outputs...
technical_matches: json
pricing_data: json
final_proposal: text
```

## Security Considerations

### Production Deployment

When deploying to production:

1. **Add file size limits**
   ```python
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
   ```

2. **Validate file types**
   ```python
   ALLOWED_TYPES = ['application/pdf', 'text/plain']
   ```

3. **Sanitize filenames**
   ```python
   import re
   filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
   ```

4. **Use cloud storage**
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage

5. **Add authentication**
   - User login required
   - File access control
   - Audit logging

## Next Steps

1. ✅ Upload your first RFP
2. ✅ Process it through the agent workflow
3. 🔲 Add more file format support
4. 🔲 Implement OCR for image PDFs
5. 🔲 Add batch upload
6. 🔲 Add file preview
7. 🔲 Export processed results

---

**Ready to upload!** The system is fully functional and ready to process your RFP documents. 📄✨
