# Google Service Account Credentials

This directory is for storing Google service account credentials for Google Sheets integration.

## Setup Instructions

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Sheets API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it
   - Search for "Google Drive API" and enable it

3. **Create a Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Click "Create and Continue"
   - Skip role assignment (or assign Viewer role)
   - Click "Done"

4. **Create and Download JSON Key**:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Download the JSON file

5. **Place the JSON file**:
   - Rename it to something like `google-service-account.json`
   - Place it in this `credentials/` directory
   - **IMPORTANT**: Add `credentials/*.json` to `.gitignore` to avoid committing secrets

6. **Share Google Sheets with Service Account**:
   - Open your Google Sheet
   - Click "Share" button
   - Add the service account email (found in the JSON file as `client_email`)
   - Give it "Viewer" or "Editor" permissions as needed

7. **Set Environment Variable**:
   ```bash
   GOOGLE_CREDENTIALS_PATH=credentials/google-service-account.json
   ```

## Security Note

**NEVER commit service account JSON files to version control!** They contain sensitive credentials.

The `.gitignore` file should already exclude `credentials/*.json` files.

