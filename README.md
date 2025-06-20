# DESAISIV-OCR

**Objective:**  
This app extracts and processes insurance claims and benefits data from PDF files. It uses `pdfplumber` to parse structured tables, cleans the data with `pandas`, and stores the results in Redis.

---

## How It Works

1. Parses metadata, claims, and benefits from a PDF.
2. Cleans and formats the extracted data.
3. Stores the results in Redis (`claims_data` and `benefits_data`).

---

## How to Run

### With Docker Compose


`docker compose up --build`

This will:

Build the image

Run the app and Redis

Process the sample PDF

Save results to Redis

