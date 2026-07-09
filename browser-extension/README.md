# Research Agent Browser Extension

Right-click any selected text on a webpage (or right-click the page itself) and send it straight to your Research Agent backend - no need to copy/paste into the app manually.

## How it works

- Select text on any page → right-click → **Research "..." with Research Agent**
- Or right-click anywhere on a page with nothing selected → **Research this page's topic** (uses the page title)
- Click the extension's icon in your Chrome toolbar to see the results

This calls your **local backend directly** (`http://localhost:8000`) - your backend must be running for this to work. It does not use the frontend at all, so the frontend doesn't even need to be running for the extension itself, though the "Open full results" link in the popup opens the frontend at `http://localhost:5173`.

## Installing it (unpacked extension, since this isn't published to the Chrome Web Store)

1. Open Chrome and go to `chrome://extensions`
2. Turn on **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select this `browser-extension` folder
5. The extension should now appear in your toolbar (you may need to click the puzzle-piece icon and pin it)

## Requirements

- Your backend must be running at `http://localhost:8000` (same as always: `uvicorn main:app --reload --reload-exclude "*.db"`)
- Your backend's `.env` must be fully set up (including `APP_SECRET`) - the extension just calls your existing backend, so anything the backend needs, it needs too
- That's it - no additional setup, no separate API keys needed here

## Notes

- This only works with your backend running **locally**. If you ever deploy the backend somewhere else, the extension's `background.js` would need its API URL updated (and the `host_permissions` in `manifest.json` too).
- Since this loads as an "unpacked" extension (not from the Chrome Web Store), Chrome will show a "Developer mode extensions" warning banner sometimes - this is normal and expected for local development, not a sign anything is wrong.
