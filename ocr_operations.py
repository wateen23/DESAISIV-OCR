import pdfplumber
import pandas as pd
import re


class PDFExtractor:
    def __init__(self, file_path: str):
        self.path = file_path

    def turn_meta_data_to_dict(self, table: list[list[str]]) -> dict:
        meta_data_dict = {}
        for row in table:
            for i in range(0, len(row) - 1, 2):
                key = row[i]
                value = row[i + 1]
                meta_data_dict[key] = value
        return meta_data_dict

    def clean_headers(self, name: str) -> str:
        seprated_name = re.sub(r"(?<=[a-zA-Z])of(?=[A-Z])", " of ", name)
        # name = re.sub(r'(?<!^)(?=[A-Z])', '', name)
        seprated_name = seprated_name.replace("\n", " ")
        print(seprated_name)
        return seprated_name

    def extract(self) -> dict:
        result = {"meta_data": [], "claims": [], "benefits": []}

        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue

                    first_row = " ".join(str(cell).lower() for cell in table[0] if cell)

                    if "groupnumber" in first_row:
                        meta_data_dict = self.turn_meta_data_to_dict(table)
                        # print(f"\n\n{meta_data_dict}\n\n")
                        result["meta_data"].extend(meta_data_dict)

                    elif "monthlyclaims" in first_row:
                        result["claims"].extend(table)

                    elif "overallbenefits" in first_row:
                        result["benefits"].extend(table)

        return result

    def preprocess_claims_df(self, tables_dict: dict):
        meta_data = tables_dict["meta_data"]
        raw_df = pd.DataFrame(tables_dict["claims"])

        old_col = raw_df.iloc[0]
        new_col = [self.clean_headers(col_name) for col_name in old_col]
        df = raw_df[1:].copy()
        df.columns = new_col

        policy_year = None
        cleaned_rows = []

        for _, row in df.iterrows():
            first_col = str(row[new_col[0]]).strip().lower()

            if "2year" in first_col:
                policy_year = "2 Years Prior"
                continue
            elif "priorpolicyyear" in first_col:
                policy_year = "Prior Policy Year"
                continue
            elif "lastpolicyyear" in first_col:
                policy_year = "Last Policy Year"
                continue
            elif "overall" in first_col:
                continue
            elif set(row.dropna().unique()) == {"0"}:
                continue

        row["Policy Year"] = policy_year
        cleaned_rows.append(row)

        cleaned_df = pd.DataFrame(cleaned_rows)
        return cleaned_df.reset_index(drop=True)


if __name__ == "__main__":
    extractor = PDFExtractor(file_path="OCR Test Template (1) (1).pdf")
    # tables = extractor.extract()
    # extractor.preprocess_claims_df(tables)
    x = "NumberofLives\nInsured"
    extractor.clean_headers(x)
