import redis
import os
from ocr_operations import PDFExtractor  #


extractor = PDFExtractor(file_path="OCR Test Template (1) (1).pdf")

tables = extractor.extract()


claims_df = extractor.preprocess_claims_df(tables)
benefits_df = extractor.preprocess_benefits_df(tables)


redis_host = os.getenv("REDIS_HOST", "localhost")  
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

r.set("claims_data", claims_df.to_json(orient="records"))
r.set("benefits_data", benefits_df.to_json(orient="records"))

print("Data saved to Redis.")
