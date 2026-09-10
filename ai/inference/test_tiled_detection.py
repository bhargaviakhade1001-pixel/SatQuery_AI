from ultralytics import YOLO
from PIL import Image

IMAGE_PATH = "ai/datasets/test.jpg"
MODEL_PATH = "yolo11n.pt"

TILE_SIZE = 640
OVERLAP = 0.2
CONFIDENCE = 0.05


def create_tiles(image):
    width, height = image.size
    step = int(TILE_SIZE * (1 - OVERLAP))

    tiles = []

    for y in range(0, height, step):
        for x in range(0, width, step):

            right = min(x + TILE_SIZE, width)
            bottom = min(y + TILE_SIZE, height)

            # Skip extremely small edge tiles
            if right - x < 200 or bottom - y < 200:
                continue

            tile = image.crop((x, y, right, bottom))

            tiles.append((tile, x, y))

    return tiles


print("Loading YOLO...")
model = YOLO(MODEL_PATH)

print("Loading image...")
image = Image.open(IMAGE_PATH).convert("RGB")

print(f"Image size: {image.size}")

tiles = create_tiles(image)

print(f"Created {len(tiles)} tiles")

detections = []

for index, (tile, offset_x, offset_y) in enumerate(tiles):

    results = model(
        tile,
        conf=CONFIDENCE,
        verbose=False
    )

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])

            detections.append(
                {
                    "class": class_name,
                    "confidence": confidence,
                    "x": offset_x,
                    "y": offset_y
                }
            )

    print(f"Processed tile {index + 1}/{len(tiles)}")


print("\n===== TILED DETECTIONS =====")

if not detections:
    print("No objects detected.")

else:
    counts = {}

    for detection in detections:

        name = detection["class"]

        counts[name] = counts.get(name, 0) + 1

    for name, count in counts.items():
        print(f"{name}: {count}")

    print(f"\nTotal detections: {len(detections)}")
