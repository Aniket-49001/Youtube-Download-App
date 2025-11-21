
# YouTube Downloader

This is a web-based application to download YouTube videos and playlists.

## How to run the project

### 1. Set up a virtual environment

It is recommended to use a virtual environment to install the dependencies.

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS and Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 3. Run the application

Start the Flask development server:
```bash
python app.py
```

The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

### 4. Open the application in your browser

Open your web browser and navigate to `http://127.0.0.1:5000`.

You can now paste a YouTube URL and use the "Get Info" button to fetch video information and download options.
