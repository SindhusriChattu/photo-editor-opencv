import cv2
import numpy as np
import streamlit as st
from PIL import Image
import io

# Try to import mediapipe for portrait background blur.
# If it is not installed / fails to load on the deployment host,
# the app still works — that one feature is just disabled.
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False


# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(page_title="Photo Editor", page_icon="🖼️", layout="wide")
st.title("🖼️ Photo Editor — OpenCV + Streamlit")
st.caption("Upload → Adjust → Apply filters → View → Download")


# ----------------------------------------------------------------------
# HELPER FUNCTIONS (all take/return a BGR numpy array, OpenCV style)
# ----------------------------------------------------------------------

def resize_image(img, scale_percent):
    width = max(1, int(img.shape[1] * scale_percent / 100))
    height = max(1, int(img.shape[0] * scale_percent / 100))
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)


def adjust_brightness_contrast(img, brightness, contrast):
    # brightness: -100 to 100, contrast: -100 to 100
    brightness = int(brightness)
    contrast = int(contrast)

    # contrast factor
    f = 131 * (contrast + 127) / (127 * (131 - contrast)) if contrast != 131 else 1
    alpha = f
    gamma = 127 * (1 - f)

    out = cv2.addWeighted(img, alpha, img, 0, gamma + brightness)
    return out


def to_grayscale(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)  # keep 3 channels for consistency


def apply_blur(img, strength):
    # strength: odd kernel size
    k = int(strength)
    if k % 2 == 0:
        k += 1
    k = max(1, k)
    return cv2.GaussianBlur(img, (k, k), 0)


def apply_sharpen(img, strength):
    # strength scales how aggressive the sharpening is
    amount = strength / 10.0
    kernel = np.array([[0, -1, 0],
                        [-1, 5 + amount, -1],
                        [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def apply_warm_filter(img, intensity):
    # Increase red / yellow tones, decrease blue tones
    img = img.astype(np.float32)
    b, g, r = cv2.split(img)
    factor = intensity / 100.0
    r = np.clip(r + 30 * factor, 0, 255)
    g = np.clip(g + 10 * factor, 0, 255)
    b = np.clip(b - 20 * factor, 0, 255)
    out = cv2.merge([b, g, r]).astype(np.uint8)
    return out


def apply_edge_detection(img, t1, t2):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, t1, t2)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def apply_sketch(img):
    gray, color_sketch = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def apply_cartoon(img):
    # Smooth colors, keep strong edges -> cartoon look
    color = cv2.bilateralFilter(img, d=9, sigmaColor=200, sigmaSpace=200)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9
    )
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.bitwise_and(color, edges_colored)


def rotate_image(img, angle):
    if angle == 0:
        return img
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, matrix, (w, h))


@st.cache_resource
def get_selfie_segmenter():
    mp_selfie = mp.solutions.selfie_segmentation
    return mp_selfie.SelfieSegmentation(model_selection=1)


def apply_portrait_blur(img, blur_strength, threshold=0.5):
    """
    Blurs the background while keeping the detected person sharp.
    Uses MediaPipe Selfie Segmentation.
    """
    segmenter = get_selfie_segmenter()
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = segmenter.process(rgb)
    mask = result.segmentation_mask  # float32, values 0-1

    condition = mask > threshold
    condition_3ch = np.stack((condition,) * 3, axis=-1)

    k = int(blur_strength)
    if k % 2 == 0:
        k += 1
    k = max(1, k)
    blurred_bg = cv2.GaussianBlur(img, (k, k), 0)

    output = np.where(condition_3ch, img, blurred_bg)
    return output.astype(np.uint8)


def cv2_to_bytes(img_bgr, fmt="PNG"):
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    return buf.getvalue()


# ----------------------------------------------------------------------
# SIDEBAR — CONTROLS
# ----------------------------------------------------------------------
st.sidebar.header("1. Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload an image", type=["jpg", "jpeg", "png", "bmp"]
)

if uploaded_file is None:
    st.info("👈 Upload an image from the sidebar to get started.")
    st.stop()

# Read uploaded file into an OpenCV (BGR) image
pil_image = Image.open(uploaded_file).convert("RGB")
original_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

st.sidebar.header("2. Resize")
scale_percent = st.sidebar.slider("Scale (%)", 10, 200, 100, step=5)

st.sidebar.header("3. Brightness & Contrast")
brightness = st.sidebar.slider("Brightness", -100, 100, 0)
contrast = st.sidebar.slider("Contrast", -100, 100, 0)

st.sidebar.header("4. Filters")
apply_gray = st.sidebar.checkbox("Grayscale")
apply_blur_toggle = st.sidebar.checkbox("Blur")
blur_strength = st.sidebar.slider("Blur strength", 1, 51, 15, step=2, disabled=not apply_blur_toggle)

apply_sharpen_toggle = st.sidebar.checkbox("Sharpen")
sharpen_strength = st.sidebar.slider("Sharpen strength", 1, 50, 10, disabled=not apply_sharpen_toggle)

apply_warm_toggle = st.sidebar.checkbox("Warm filter")
warm_intensity = st.sidebar.slider("Warm intensity", 0, 100, 50, disabled=not apply_warm_toggle)

st.sidebar.header("5. Portrait Background Blur")
if MEDIAPIPE_AVAILABLE:
    apply_portrait = st.sidebar.checkbox("Blur background (portrait mode)")
    portrait_strength = st.sidebar.slider(
        "Background blur strength", 5, 71, 35, step=2, disabled=not apply_portrait
    )
else:
    apply_portrait = False
    st.sidebar.info("mediapipe not installed — portrait blur disabled.")

st.sidebar.header("6. Optional Extras")
apply_edges = st.sidebar.checkbox("Edge detection")
edge_t1 = st.sidebar.slider("Edge threshold 1", 0, 300, 100, disabled=not apply_edges)
edge_t2 = st.sidebar.slider("Edge threshold 2", 0, 300, 200, disabled=not apply_edges)

apply_sketch_toggle = st.sidebar.checkbox("Sketch effect")
apply_cartoon_toggle = st.sidebar.checkbox("Cartoon effect")
rotation_angle = st.sidebar.slider("Rotate (degrees)", -180, 180, 0)


# ----------------------------------------------------------------------
# PIPELINE — APPLY EDITS IN ORDER
# ----------------------------------------------------------------------
edited = original_img.copy()
edited = resize_image(edited, scale_percent)
edited = adjust_brightness_contrast(edited, brightness, contrast)

if apply_gray:
    edited = to_grayscale(edited)

if apply_blur_toggle:
    edited = apply_blur(edited, blur_strength)

if apply_sharpen_toggle:
    edited = apply_sharpen(edited, sharpen_strength)

if apply_warm_toggle:
    edited = apply_warm_filter(edited, warm_intensity)

if apply_portrait and MEDIAPIPE_AVAILABLE:
    try:
        edited = apply_portrait_blur(edited, portrait_strength)
    except Exception as e:
        st.warning(f"Portrait blur failed: {e}")

if apply_edges:
    edited = apply_edge_detection(edited, edge_t1, edge_t2)

if apply_sketch_toggle:
    edited = apply_sketch(edited)

if apply_cartoon_toggle:
    edited = apply_cartoon(edited)

edited = rotate_image(edited, rotation_angle)


# ----------------------------------------------------------------------
# DISPLAY — BEFORE / AFTER
# ----------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Original")
    st.image(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB), use_container_width=True)

with col2:
    st.subheader("Edited")
    st.image(cv2.cvtColor(edited, cv2.COLOR_BGR2RGB), use_container_width=True)


# ----------------------------------------------------------------------
# DOWNLOAD
# ----------------------------------------------------------------------
st.header("Download")
download_format = st.selectbox("Format", ["PNG", "JPEG"])
img_bytes = cv2_to_bytes(edited, fmt=download_format)

st.download_button(
    label=f"⬇️ Download edited image ({download_format})",
    data=img_bytes,
    file_name=f"edited_image.{download_format.lower()}",
    mime=f"image/{download_format.lower()}",
)
