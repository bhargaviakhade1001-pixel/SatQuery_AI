import os

import yolov5
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# LOAD xView YOLO MODEL
# ============================================================

print("Loading xView detection model...")

model = yolov5.load(
    "deprem-ml/Binafarktespit-yolo5x-v1-xview"
)

model.conf = 0.40

print("xView detection model loaded successfully!")


# ============================================================
# CLASSES WE WANT FOR SATQUERY
# ============================================================

ALLOWED_CLASSES = {
    "Building",
    "Small Car",
    "Passenger Car",
    "Truck",
    "Cargo Truck",
    "Truck w/Box",
    "Bus",
    "Excavator",
}

YOLO_FILTERS = {
    "building": ["Building"],
    "car": ["Small Car", "Passenger Car"],
    "truck": ["Truck", "Cargo Truck", "Truck w/Box"],
    "bus": ["Bus"],
    "excavator": ["Excavator"],
}


# ============================================================
# DETECTION
# ============================================================

def detect_objects(
    image_path,
    output_path=None,
    requested_class=None,
    show_all=True,
):
    """
    Run xView object detection on an image.

    Returns:
        {
            "counts": {
                "Building": 37,
                "Small Car": 5
            },
            "detections": [
                {
                    "class": "Building",
                    "confidence": 0.87,
                    "box": [x1, y1, x2, y2]
                }
            ],
            "annotated_image": "/path/to/output.jpg"
        }
    """

    # --------------------------------------------------------
    # Check input image
    # --------------------------------------------------------

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # --------------------------------------------------------
    # Run YOLO
    # --------------------------------------------------------

    results = model(
        image_path,
        size=1280
    )

    detections = results.pred[0]

    # --------------------------------------------------------
    # Load image for drawing
    # --------------------------------------------------------

    image = Image.open(image_path).convert("RGB")

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Try to load a font
    # --------------------------------------------------------

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            16
        )
    except Exception:
        font = ImageFont.load_default()

    # --------------------------------------------------------
    # Detection containers
    # --------------------------------------------------------

    counts = {}
    detection_list = []

    # --------------------------------------------------------
    # Process detections
    # --------------------------------------------------------

    for detection in detections:

        x1, y1, x2, y2 = detection[:4]

        confidence = float(detection[4])

        class_id = int(detection[5])

        class_name = results.names[class_id]

        # Ignore classes we don't currently need
        if class_name not in ALLOWED_CLASSES:
          continue

# ----------------------------------------------------
# Filter only requested objects
# ----------------------------------------------------

        if not show_all and requested_class:

            allowed = YOLO_FILTERS.get(requested_class, [])

            if class_name not in allowed:
                continue

        # Convert coordinates to integers
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # ----------------------------------------------------
        # Count object
        # ----------------------------------------------------

        counts[class_name] = (
            counts.get(class_name, 0) + 1
        )

        # ----------------------------------------------------
        # Store detection information
        # ----------------------------------------------------

        detection_list.append(
            {
                "class": class_name,
                "confidence": round(confidence, 3),
                "box": [x1, y1, x2, y2],
            }
        )

        # ----------------------------------------------------
        # Draw bounding box
        # ----------------------------------------------------

        draw.rectangle(
            [x1, y1, x2, y2],
            outline="red",
            width=3,
        )

        # ----------------------------------------------------
        # Draw label
        # ----------------------------------------------------

        label = f"{class_name} {confidence:.2f}"

        bbox = draw.textbbox(
            (x1, y1),
            label,
            font=font,
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Keep label inside image
        label_y = max(
            0,
            y1 - text_height - 4
        )

        draw.rectangle(
            [
                x1,
                label_y,
                x1 + text_width + 6,
                label_y + text_height + 4,
            ],
            fill="red",
        )

        draw.text(
            (x1 + 3, label_y + 2),
            label,
            fill="white",
            font=font,
        )

    # --------------------------------------------------------
    # Save annotated image
    # --------------------------------------------------------

    if output_path is None:

        base_name = os.path.splitext(
            os.path.basename(image_path)
        )[0]

        output_path = os.path.join(
            os.path.dirname(image_path),
            f"{base_name}_detected.jpg",
        )

    image.save(output_path, quality=95)

    print(
        f"Annotated detection image saved to: {output_path}"
    )

    # --------------------------------------------------------
    # Return complete detection result
    # --------------------------------------------------------

    return {
    "counts": counts,
    "total_objects": sum(counts.values()),
    "requested_class": requested_class,
    "detections": detection_list,
    "annotated_image": output_path,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    image_path = "ai/datasets/test.jpg"

    print(
        "\n===== SatQuery Object Detection ====="
    )

    results = detect_objects(image_path)

    # --------------------------------------------------------
    # Print counts
    # --------------------------------------------------------

    print("\n===== COUNTS =====")

    if not results["counts"]:
        print("No relevant objects detected.")

    else:
        for name, count in sorted(
            results["counts"].items()
        ):
            print(
                f"{name}: {count}"
            )

    # --------------------------------------------------------
    # Print individual detections
    # --------------------------------------------------------

    print(
        "\n===== DETECTIONS ====="
    )

    for detection in results["detections"]:

        print(
            f"{detection['class']} | "
            f"confidence={detection['confidence']} | "
            f"box={detection['box']}"
        )

    print(
        "\nAnnotated image:"
    )

    print(
        results["annotated_image"]
    )
