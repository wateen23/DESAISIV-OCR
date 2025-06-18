import pdfplumber 
import pandas as pd

class PDFExtractor:
    def __init__(self, file_path:str):
        self.path = file_path

    def extract(self) -> dict:
        result = {
            "meta_data": [],
            "claims": [],
            "benefits": []
        }

        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue

                    first_row = " ".join(str(cell).lower() for cell in table[0] if cell)
        
                    if "groupnumber" in first_row:
                        result["meta_data"].extend(table)

                    elif "monthlyclaims" in first_row:
                        result["claims"].extend(table)

                    elif "overallbenefits" in first_row:
                        result["benefits"].extend(table)

        return result

    def preprocess(self, tables_dict:dict):
        pass


if __name__ == "__main__":
    extractor = PDFExtractor(file_path="OCR Test Template (1) (1).pdf")
    extractor.extract()
