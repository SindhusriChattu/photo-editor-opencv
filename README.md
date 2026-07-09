# Photo Editor — OpenCV + Streamlit

A simple, browser-based photo editor built with **OpenCV** and **Streamlit**.
Upload an image, adjust it with sliders, apply filters, and download the result — all in one page.

## Live Demo
[Add your Streamlit Cloud link here after deployment]

## Features

| Feature | Description |
|---|---|
| Upload | Upload any JPG / PNG / BMP image |
| Resize | Scale image from 10% to 200% |
| Brightness & Contrast | Adjustable via sliders |
| Grayscale | One-click black & white conversion |
| Blur | Adjustable Gaussian blur |
| Sharpen | Adjustable sharpening strength |
| Warm filter | Adds a warm, golden-hour tone |
| Portrait background blur | Detects the person (MediaPipe Selfie Segmentation) and blurs only the background |
| Edge detection | Canny edge detection with adjustable thresholds |
| Sketch effect | Pencil-sketch style output |
| Cartoon effect | Cartoon-style stylization |
| Rotate | Rotate image -180° to 180° |
| Download | Download the final edited image as PNG or JPEG |

## How It Works (Flow)

```
Upload Image
     |
     v
Adjust (resize, brightness, contrast)
     |
     v
Apply Filters (grayscale / blur / sharpen / warm /
               portrait blur / edge / sketch / cartoon / rotate)
     |
     v
View (Original vs Edited side-by-side)
     |
     v
Download Edited Image
```

## Tech Stack

- Python
- OpenCV (image processing)
- MediaPipe (Selfie Segmentation for portrait background blur)
- Streamlit (UI + deployment)
- Pillow / NumPy

## Project Structure

```
photo-editor/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md
```

## Run Locally

1. Clone the repository
   ```
   git clone https://github.com/SindhusriChattu/photo-editor.git
   cd photo-editor
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Run the app
   ```
   streamlit run app.py
   ```

4. Open the local URL shown in the terminal (usually `http://localhost:8501`)

## Deploy on Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select this repository and branch, and set the main file to `app.py`.
4. Click **Deploy**.

> Note: If MediaPipe causes a build issue on Streamlit Cloud, the app still works —
> the portrait background blur feature is automatically disabled if MediaPipe fails to import,
> and every other feature keeps working.

## Author

Sindhu Sri Chattu
- GitHub: [SindhusriChattu](https://github.com/SindhusriChattu)
- LinkedIn: [Sindhu Sri Chattu](https://www.linkedin.com/in/sindhu-sri-chattu-a9005a2b4)

Built as part of Computer Vision portfolio work at Innomatics Research Labs.
