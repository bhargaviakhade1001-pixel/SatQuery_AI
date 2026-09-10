
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ai.router.query_router import classify_query
from ai.inference.detection import detect_objects

from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

import uuid
import asyncio
import io
import os
import tempfile


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = FastAPI(title="SatQuery AI Backend")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://satquery-ai-hazel.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured in .env"
    )

client = genai.Client(api_key=api_key)


# ============================================================
# IMAGE CONFIGURATION
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "image/webp",
}


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

OUTPUT_DIR = "outputs"
DETECTION_OUTPUT_DIR = os.path.join(
    OUTPUT_DIR,
    "detections",
)

os.makedirs(
    DETECTION_OUTPUT_DIR,
    exist_ok=True,
)


# Serve generated images to the frontend
app.mount(
    "/outputs",
    StaticFiles(directory=OUTPUT_DIR),
    name="outputs",
)


# ============================================================
# HELPERS
# ============================================================

def validate_image_type(image: UploadFile) -> None:
    """Validate uploaded image MIME type."""

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are supported.",
        )


async def read_and_validate_image(
    image: UploadFile,
) -> bytes:
    """Read and validate an uploaded image."""

    validate_image_type(image)

    image_data = await image.read()

    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="Image file is empty.",
        )

    try:
        img = Image.open(
            io.BytesIO(image_data)
        )

        img.verify()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file.",
        )

    return image_data


async def run_gemini_image_analysis(
    image_data: bytes,
    mime_type: str,
    prompt: str,
) -> str:
    """Send an image and prompt to Gemini."""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_text(
                    text=prompt
                ),
                types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type,
                ),
            ],
        )

        analysis = response.text

        if not analysis:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"VLM analysis failed: {repr(e)}",
        )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "SatQuery AI Backend is running",
        "status": "success",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# IMAGE UPLOAD
# ============================================================

@app.post("/api/upload-image")
async def upload_image(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    return {
        "status": "success",
        "filename": image.filename,
        "content_type": image.content_type,
        "size": len(image_data),
        "message": "Satellite image uploaded successfully.",
    }


# ============================================================
# ANALYZE IMAGE
# ============================================================

@app.post("/api/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    query: str = Form(...),
):
    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    # --------------------------------------------------------
    # Read and validate image
    # --------------------------------------------------------

    image_data = await read_and_validate_image(
        image
    )

    # --------------------------------------------------------
    # Classify user query
    # --------------------------------------------------------

    route_info = classify_query(query)

    route = route_info["route"]
    requested_class = route_info.get("requested_class")
    show_all = route_info.get("show_all", True)

    print(f"Query: {query}")
    print(f"Route Info: {route_info}")

    # ========================================================
    # OBJECT DETECTION
    # ========================================================

    if route == "detection":

        temp_image_path = None

        try:
            # ------------------------------------------------
            # Create temporary image
            # ------------------------------------------------

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg",
            ) as temp_file:

                temp_file.write(
                    image_data
                )

                temp_image_path = (
                    temp_file.name
                )

            # ------------------------------------------------
            # Create output filename
            # ------------------------------------------------

            output_path = os.path.join(
                DETECTION_OUTPUT_DIR,
                f"detected_{uuid.uuid4().hex}.jpg",
            )

            # ------------------------------------------------
            # Run YOLO
            # ------------------------------------------------

            detection_result = detect_objects(
                temp_image_path,
                output_path=output_path,
                requested_class=requested_class,
                show_all=show_all,
            )

            # ------------------------------------------------
            # Extract results
            # ------------------------------------------------

            counts = detection_result[
                "counts"
            ]

            detections = detection_result[
                "detections"
            ]

            annotated_image = detection_result[
                "annotated_image"
            ]

            # ------------------------------------------------
            # Create human-readable analysis
            # ------------------------------------------------

            if not counts:

                analysis = (
                    "No relevant objects were detected."
                )

            else:

                analysis_lines = []

                for name, count in sorted(
                    counts.items()
                ):
                    analysis_lines.append(
                        f"{name}: {count}"
                    )

                analysis = "\n".join(
                    analysis_lines
                )

            # ------------------------------------------------
            # Convert image path to frontend URL
            # ------------------------------------------------

            relative_image_path = os.path.relpath(
                annotated_image,
                OUTPUT_DIR,
            )

            annotated_image_url = (
                "/outputs/"
                + relative_image_path.replace(
                    os.sep,
                    "/",
                )
            )

            # ------------------------------------------------
            # Return detection result
            # ------------------------------------------------

            return {
                "status": "success",
                "route": "detection",
                "query_type": (
                    "all_objects"
                    if show_all
                    else "specific_object"
                ),
                "requested_class": requested_class,
                "filename": image.filename,
                "query": query,
                "analysis": analysis,
                "counts": counts,
                "total_objects": sum(counts.values()),
                "detections": detections,
                "annotated_image": annotated_image_url,
            }

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Object detection failed: "
                    f"{str(e)}"
                ),
            )

        finally:

            # ----------------------------------------------
            # Delete temporary input image
            # ----------------------------------------------

            if (
                temp_image_path
                and os.path.exists(
                    temp_image_path
                )
            ):
                os.remove(
                    temp_image_path
                )

    # ========================================================
    # SEGMENTATION
    # ========================================================

    if route == "segmentation":

        return {
            "status": "success",
            "route": "segmentation",
            "query": query,
            "analysis": (
                "Segmentation module is not "
                "connected yet."
            ),
        }

    # ========================================================
    # GENERAL GEMINI IMAGE ANALYSIS
    # ========================================================

    prompt = f"""
You are SatQuery AI, an assistant specialized in
remote sensing and satellite image analysis.

Analyze the provided image and answer the user's question.

User question:
{query}

Describe only what can reasonably be observed in the image.

Pay attention to visible features such as:

- Vegetation
- Buildings
- Roads
- Water bodies
- Agricultural land
- Open land
- Urban areas
- Other significant visible features

Do not invent information that cannot be determined
from the image.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "route": route,
        "filename": image.filename,
        "query": query,
        "analysis": analysis,
    }


# ============================================================
# WHAT CHANGED
# SATELLITE IMAGE COMPARISON
# ============================================================

@app.post("/api/change-detection")
async def change_detection(
    old_image: UploadFile = File(...),
    new_image: UploadFile = File(...),
):
    old_data = await read_and_validate_image(
        old_image
    )

    new_data = await read_and_validate_image(
        new_image
    )

    prompt = """
You are SatQuery AI, an assistant specialized in
satellite and remote sensing image analysis.

You are given TWO overhead images of an area.

The first image is the OLD image.
The second image is the NEW image.

Compare the two images carefully.

Identify only changes that are visibly supported
by the images.

Analyze these categories:

1. Construction or buildings
2. Vegetation or greenery
3. Roads and infrastructure
4. Water bodies or water coverage
5. Urban development
6. Open land

For each category, report:

- Detected
- No major visible change
- Uncertain

Then provide a short overall summary.

Do not invent changes that cannot be visually confirmed.
Do not assume the exact dates of the images.
Do not claim that construction is legal or illegal.

Return the answer in a clear, simple format suitable
for a normal user.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_text(
                    text=prompt
                ),
                types.Part.from_text(
                    text="OLD IMAGE:"
                ),
                types.Part.from_bytes(
                    data=old_data,
                    mime_type=old_image.content_type,
                ),
                types.Part.from_text(
                    text="NEW IMAGE:"
                ),
                types.Part.from_bytes(
                    data=new_data,
                    mime_type=new_image.content_type,
                ),
            ],
        )

        analysis = response.text

        if not analysis:
            raise ValueError(
                "Gemini returned an empty response."
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Change detection failed: "
                f"{repr(e)}"
            ),
        )

    return {
        "status": "success",
        "feature": "What Changed?",
        "old_filename": old_image.filename,
        "new_filename": new_image.filename,
        "analysis": analysis,
    }


# ============================================================
# FLOOD RISK ANALYSIS
# ============================================================

@app.post("/api/flood-risk")
async def flood_risk(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, an assistant specialized in
satellite and remote sensing image analysis.

Analyze this overhead/satellite image specifically for
VISIBLE INDICATORS RELATED TO FLOOD RISK.

Look carefully for:

- Visible water bodies
- Water expansion or flooding
- Low-lying or open areas
- Possible water accumulation areas
- Drainage channels if visible
- Rivers, lakes, ponds or other nearby water
- Dense urban areas where water accumulation may be possible
- Vegetation or agricultural areas that appear waterlogged

Give an AI-assisted visual assessment:

Flood Risk:
LOW / MEDIUM / HIGH / UNCERTAIN

Then explain the main visible reasons.

IMPORTANT:

- Only use evidence visible in the image.
- Do not invent elevation, rainfall, drainage,
  historical flood records, or weather information.
- Satellite imagery alone cannot guarantee whether
  an area will flood.
- This is an AI-assisted visual assessment, not an
  official flood warning or engineering assessment.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Flood Risk",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# CONSTRUCTION CHECK
# ============================================================

@app.post("/api/construction-check")
async def construction_check(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, specialized in satellite and
remote sensing image analysis.

Analyze this overhead/satellite image specifically
for visible signs of construction and development.

Look for:

- Buildings
- Newly developed structures
- Construction sites
- Cleared land
- New roads or infrastructure
- Expansion of built-up areas
- Changes from open land to developed land

Give an assessment:

Construction Activity:
DETECTED / NOT CLEARLY DETECTED / UNCERTAIN

Then explain the visible evidence in simple language.

IMPORTANT:

- Only describe what is visibly supported by the image.
- Do not claim that construction is legal or illegal.
- Do not determine ownership of land.
- Do not assume permits or approvals.
- Satellite imagery alone cannot confirm legal compliance.

If construction appears present, recommend verifying
permits, zoning, approved plans, and land records with
the relevant local authority.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Construction Check",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# ENVIRONMENT / GREENERY ANALYSIS
# ============================================================

@app.post("/api/environment")
async def environment_analysis(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, specialized in satellite and
remote sensing image analysis.

Analyze this overhead/satellite image specifically
for ENVIRONMENT AND GREENERY.

Look for visible:

- Trees and vegetation
- Green areas
- Forest-like areas
- Agricultural fields
- Open land
- Bare or exposed land
- Areas with dense vegetation
- Areas with sparse vegetation
- Visible signs of vegetation loss or land clearing

Give a simple assessment:

GREENERY LEVEL:
LOW / MEDIUM / HIGH / UNCERTAIN

Then explain the main visible reasons.

Also describe the major environmental features
visible in the image.

IMPORTANT:

- Only use evidence visible in the image.
- Do not calculate NDVI from an ordinary RGB image.
- Do not invent environmental measurements.
- Do not claim exact vegetation percentages.
- Do not assume the health of vegetation unless it
  can reasonably be observed.
- This is an AI-assisted visual assessment.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Environment / Greenery",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# AGRICULTURE ANALYSIS
# ============================================================

@app.post("/api/agriculture")
async def agriculture_analysis(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, specialized in satellite and
remote sensing image analysis.

Analyze this overhead/satellite image specifically
for AGRICULTURAL FEATURES.

Look for visible:

- Agricultural fields
- Crop field patterns
- Different field boundaries
- Green or vegetated farmland
- Bare agricultural land
- Irrigated-looking areas if visibly supported
- Possible waterlogged areas
- Roads or paths through agricultural land
- Signs of urban development near farmland

Give a simple assessment:

AGRICULTURAL LAND:
PRESENT / NOT CLEARLY VISIBLE / UNCERTAIN

VEGETATION CONDITION:
GOOD / MIXED / SPARSE / UNCERTAIN

Then explain the visible evidence.

IMPORTANT:

- Only use evidence visible in the image.
- Do not identify the exact crop unless clearly visible.
- Do not calculate NDVI from an ordinary RGB image.
- Do not claim exact crop health or yield.
- Do not invent rainfall, soil, irrigation, or weather data.
- This is an AI-assisted visual assessment.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Agriculture",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# DISASTER ASSESSMENT
# ============================================================

@app.post("/api/disaster")
async def disaster_analysis(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, specialized in satellite and
remote sensing image analysis.

Analyze this overhead/satellite image for VISIBLE
INDICATORS OF POSSIBLE DISASTER OR DAMAGE.

Look for:

- Flooding or unusual water spread
- Burned or fire-affected areas
- Landslide-like disturbed terrain
- Major vegetation damage
- Possible storm or cyclone-related damage
- Damaged or disrupted buildings
- Damaged roads or infrastructure
- Other significant visible disturbances

First identify the most relevant visible indicator.

Give a simple assessment:

DISASTER INDICATOR:
DETECTED / NOT CLEARLY DETECTED / UNCERTAIN

TYPE:
FLOOD / FIRE / LANDSLIDE / STORM DAMAGE /
INFRASTRUCTURE DAMAGE / OTHER / NONE

Then explain the visible evidence.

IMPORTANT:

- Only use evidence visible in the image.
- Do not claim that an official disaster is occurring.
- Do not invent weather, rainfall, earthquake,
  emergency, or government information.
- Do not estimate casualties or financial damage.
- Do not identify an event solely from assumptions.
- This is an AI-assisted visual assessment.
- Emergency decisions must rely on official authorities
  and verified disaster information.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Disaster Assessment",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# TRAFFIC ROUTE
# ============================================================

class TrafficRouteRequest(BaseModel):
    start: str
    destination: str


@app.post("/api/traffic-route")
async def traffic_route(
    request: TrafficRouteRequest,
):
    if not request.start.strip():
        raise HTTPException(
            status_code=400,
            detail="Starting location is required.",
        )

    if not request.destination.strip():
        raise HTTPException(
            status_code=400,
            detail="Destination is required.",
        )

    prompt = f"""
You are SatQuery AI, a smart location and route assistant.

The user wants to travel from:

START:
{request.start}

DESTINATION:
{request.destination}

Provide a simple route-planning response.

Include:

- Starting location
- Destination
- Suggested route
- Approximate travel considerations
- Possible alternative route
- Road or traffic considerations if known

IMPORTANT:

You do not have access to live traffic data in this
endpoint. Do not claim that traffic conditions are live
or current.

Clearly state that actual travel time and traffic may
change based on current road conditions.

Return the answer in simple language.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        analysis = response.text

        if not analysis:
            raise ValueError(
                "Gemini returned an empty response."
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Traffic route analysis failed: "
                f"{repr(e)}"
            ),
        )

    return {
        "status": "success",
        "feature": "Traffic Route",
        "start": request.start,
        "destination": request.destination,
        "analysis": analysis,
    }


# ============================================================
# PROPERTY INTELLIGENCE
# ============================================================

@app.post("/api/property-risk")
async def property_risk(
    image: UploadFile = File(...),
):
    image_data = await read_and_validate_image(
        image
    )

    prompt = """
You are SatQuery AI, a satellite and remote sensing
assistant helping users investigate an area before
making a property-related decision.

Analyze the provided overhead/satellite image.

Look for visible indicators related to:

1. FLOOD / WATER
   - Nearby visible water bodies
   - Water spread
   - Possible water accumulation areas

2. DEVELOPMENT
   - Buildings
   - Built-up areas
   - Recent-looking development
   - Roads and infrastructure

3. ENVIRONMENT
   - Vegetation
   - Green areas
   - Open land
   - Bare land

4. LAND USE
   - Residential-looking areas
   - Agricultural-looking areas
   - Commercial/industrial-looking areas
   - Open land

Give a simple area assessment.

Include:

FLOOD INDICATOR:
LOW / MEDIUM / HIGH / UNCERTAIN

DEVELOPMENT:
LOW / MEDIUM / HIGH / UNCERTAIN

GREENERY:
LOW / MEDIUM / HIGH / UNCERTAIN

LAND USE:
Describe the most likely visible land use.

OVERALL ASSESSMENT:
LOW CONCERN / MODERATE CONCERN /
HIGH CONCERN / UNCERTAIN

Then provide:

THINGS TO INVESTIGATE:
- Up to 4 important points.

IMPORTANT:

- Only use information visibly supported by the image.
- Do not claim exact property ownership.
- Do not determine whether construction is legal.
- Do not guarantee that a property is safe.
- Do not provide legal or financial certification.
- Do not invent flood history, elevation, rainfall,
  soil data, property records, or government information.
- Satellite imagery alone is not sufficient for a final
  property purchasing decision.

Clearly state that the result is an AI-assisted visual
assessment and that official records and professional
verification should be used before making a property decision.

Return the answer in simple language.
"""

    analysis = await run_gemini_image_analysis(
        image_data,
        image.content_type,
        prompt,
    )

    return {
        "status": "success",
        "feature": "Property Intelligence",
        "filename": image.filename,
        "analysis": analysis,
    }


# ============================================================
# ASK SATQUERY - TEXT ONLY CHAT
# ============================================================

@app.post("/api/chat")
async def ask_satquery(
    question: str = Form(...),
):
    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question is required.",
        )

    prompt = f"""
You are SatQuery AI, a helpful AI assistant specializing in:

- Remote sensing
- Satellite imagery
- Geography
- Environmental analysis
- Agriculture
- Disaster assessment
- Urban development
- GIS concepts

You are currently operating in TEXT-ONLY CHAT MODE.

Answer the user's question clearly and accurately.

IMPORTANT:

- You cannot see or analyze images through this chat endpoint.
- Do not pretend that you can see an image.
- If the user asks about a specific image that has not been
  provided, explain briefly that you cannot inspect that image
  through text-only chat.
- For general questions about satellite imagery, remote sensing,
  geography, and related topics, answer normally.
- Do not invent satellite data, live location data, property
  records, weather data, or other information you do not have.

User question:
{question}
"""

    last_error = None

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return {
                "status": "success",
                "feature": "Ask SatQuery",
                "question": question,
                "response": response.text,
            }

        except Exception as e:

            last_error = e

            if attempt < 2:
                await asyncio.sleep(2)

    raise HTTPException(
        status_code=503,
        detail=(
            "SatQuery AI is temporarily busy. "
            "Please try again in a moment. "
            f"Last error: {repr(last_error)}"
        ),
    )


# ============================================================
# GPS LOCATION
# ============================================================

class LocationRequest(BaseModel):
    latitude: float
    longitude: float


@app.post("/api/location")
async def save_location(
    location: LocationRequest,
):
    return {
        "status": "success",
        "feature": "GPS Location",
        "latitude": location.latitude,
        "longitude": location.longitude,
        "message": "Location received successfully.",
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get(
            "PORT",
            8000,
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )

