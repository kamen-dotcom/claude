# Google Sheets Integration Setup Guide

This guide will help you connect your questionnaire form to Google Sheets to automatically store responses.

## Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it "Survey Responses" (or any name you prefer)
4. In the first row, add these column headers:
   - A1: `Timestamp`
   - B1: `Name`
   - C1: `Age Group`
   - D1: `Occupation`
   - E1: `Interests`
   - F1: `Comments`
   - G1: `Source`

## Step 2: Create Google Apps Script

1. In your Google Sheet, click **Extensions** → **Apps Script**
2. Delete any existing code in the script editor
3. Copy and paste this code:

```javascript
function doPost(e) {
  try {
    // Get the active spreadsheet
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // Parse the incoming data
    var data = JSON.parse(e.postData.contents);

    // Append a new row with the data
    sheet.appendRow([
      data.timestamp,
      data.name,
      data.ageGroup,
      data.occupation,
      data.interests,
      data.comments,
      data.source
    ]);

    // Return success response
    return ContentService.createTextOutput(JSON.stringify({
      'result': 'success',
      'row': sheet.getLastRow()
    })).setMimeType(ContentService.MimeType.JSON);

  } catch(error) {
    // Return error response
    return ContentService.createTextOutput(JSON.stringify({
      'result': 'error',
      'error': error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

4. Click the **Save** icon (💾) or press Ctrl+S
5. Name your project (e.g., "Survey Form Handler")

## Step 3: Deploy the Script

1. Click the **Deploy** button → **New deployment**
2. Click the gear icon ⚙️ next to "Select type"
3. Select **Web app**
4. Configure the deployment:
   - **Description**: "Survey Form v1" (or any description)
   - **Execute as**: Select **Me** (your email)
   - **Who has access**: Select **Anyone**
5. Click **Deploy**
6. You may need to authorize the script:
   - Click **Authorize access**
   - Choose your Google account
   - Click **Advanced** → **Go to [Project Name] (unsafe)**
   - Click **Allow**
7. **IMPORTANT**: Copy the **Web app URL** that appears
   - It will look like: `https://script.google.com/macros/s/AKfycby.../exec`

## Step 4: Update Your HTML File

1. Open the `index.html` file
2. Find this line near the top of the `<script>` section:
   ```javascript
   const SCRIPT_URL = 'YOUR_GOOGLE_SCRIPT_URL_HERE';
   ```
3. Replace `'YOUR_GOOGLE_SCRIPT_URL_HERE'` with your actual Web app URL:
   ```javascript
   const SCRIPT_URL = 'https://script.google.com/macros/s/AKfycby.../exec';
   ```
4. Save the file
5. Commit and push to GitHub

## Step 5: Test Your Form

1. Wait 1-2 minutes for GitHub Pages to update
2. Go to your questionnaire URL: `https://kamen-dotcom.github.io/claude/`
3. Fill out and submit the form
4. Check your Google Sheet - you should see a new row with the response!

## Troubleshooting

**Problem: Responses not appearing in Google Sheet**
- Make sure you copied the correct Web app URL
- Verify the script is deployed as "Anyone" can access
- Check that the column headers in your sheet match exactly

**Problem: Authorization errors**
- Re-deploy the script
- Make sure you clicked "Allow" when authorizing
- Try using an incognito browser window

**Problem: CORS errors in browser console**
- This is normal! We use `mode: 'no-cors'` which means the browser won't show detailed errors
- As long as data appears in your Google Sheet, everything is working

## Viewing Your Responses

Simply open your Google Sheet at any time to see all submitted responses. You can:
- Sort and filter responses
- Create charts and graphs
- Export to Excel or PDF
- Share with others

## Security Note

The form sends data directly to Google Sheets. The "Anyone" access means anyone with the script URL can submit data. This is standard for public forms. If you need more security, consider:
- Using Google Forms instead
- Adding authentication to your form
- Implementing rate limiting in the Apps Script

---

**Need help?** Check the [Apps Script documentation](https://developers.google.com/apps-script)
