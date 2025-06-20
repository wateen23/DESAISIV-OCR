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

    def clean_claims_headers(self, name: str) -> str:
         
        name = re.sub(r"(?<=[a-zA-Z])of(?=[A-Z])", " of ", name)
        name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
        name = name.replace("\n", " ").strip()
        name = re.sub(r"\s+", " ", name)
        
        return name
    
    def clean_benefit_headers(self, name: str) -> str:
        if not isinstance(name, str):
            return ""
        
        name = name.replace("\n", " ").strip()
        name = re.sub(r"\s+", " ", name).lower()

        key = re.sub(r"[^a-z0-9]", "", name)

        mapping = {
            "benefitsama": "Benefit Sama",
            "numberofpaidclaims": "Number of Claims",
            "amountofpaidclaims": "Amount of Claims",
            "amtofclaimsvat": "Amount of Claims with VAT",
            "notes": "Notes"
        }

        return mapping.get(key, name)  




    def extract(self) -> dict:
        result = {"meta_data": {}, "claims": [], "benefits": []}

        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue

                    first_row = " ".join(str(cell).lower() for cell in table[0] if cell)

                    if "groupnumber" in first_row:
                        meta_data_dict = self.turn_meta_data_to_dict(table)

                        result["meta_data"]=meta_data_dict

                    elif "monthlyclaims" in first_row:
                        result["claims"].extend(table)

                    elif "overallbenefits" in first_row:
                        result["benefits"].extend(table)

        return result

    def preprocess_claims_df(self, tables_dict: dict):
        meta_data = tables_dict["meta_data"]
        raw_df = pd.DataFrame(tables_dict["claims"])

        old_col = raw_df.iloc[0]
        new_col = [self.clean_claims_headers(col_name) for col_name in old_col]
        df = raw_df[1:].copy()
        df.columns = new_col

        policy_year = None
        cleaned_rows = []

        for _, row in df.iterrows():
            
            if pd.isna(row[new_col[0]]) or not str(row[new_col[0]]).strip():
                continue

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
            elif set(str(val).strip() for val in row.dropna().unique()) == {"0"}:
                continue

            row["Policy Year"] = policy_year
            cleaned_rows.append(row)


        cleaned_df = pd.DataFrame(cleaned_rows)
        claims_df = cleaned_df.reset_index(drop=True)
        end_date = meta_data.get("PolicyExpiryDate")
        if end_date:
            end_date = end_date.replace(",", "")
            try:
                end_date = pd.to_datetime(end_date, format="%b%d%Y").strftime("%Y-%m-%d")
            except:
                end_date = None

        overall_limit = meta_data.get("OverallBenefitLimit")
        if overall_limit:
            overall_limit = overall_limit.replace(",", "")

        claims_df["End date"] = end_date
        claims_df["Class"] = meta_data.get("Class")
        claims_df["Overall Limit"] = overall_limit

      
        print(claims_df)
        return claims_df
    
    def preprocess_benefits_df(self, tables_dict: dict):
        meta_data = tables_dict["meta_data"]
        raw_df = pd.DataFrame(tables_dict["benefits"])
        

        # === Find the correct header row ===
        old_col = None
        for idx, row in raw_df.iterrows():
            row_strs = [str(cell).strip().lower() for cell in row if pd.notna(cell)]
            if (
                "benefit_sama" in row_strs
                and "numberofpaidclaims" in row_strs
                and "amountofpaidclaims" in row_strs
            ):
                old_col = row
                df = raw_df[idx + 1:].copy()
                break

        if old_col is None:
            raise ValueError("❌ Could not locate the header row for benefits table.")

        new_col = [self.clean_benefit_headers(col_name) for col_name in old_col]
        df.columns = new_col

        cleaned_rows = []
        for _, row in df.iterrows():
            benefit_raw = str(row.get("Benefit Sama", "")).strip().lower()

            if not benefit_raw or "overall" in benefit_raw:
                continue

            benefit_name = re.sub(r"^\d+\.", "", str(row["Benefit Sama"])).strip()

            notes_raw = str(row.get("Notes", "")).strip().lower()
            if "cesarean" in notes_raw:
                note = "yes"
            elif "%" in notes_raw:
                match = re.search(r"\d+%", notes_raw)
                note = match.group(0) if match else "No info"
            elif notes_raw == "":
                note = "No info"
            else:
                note = "No info"

            try:
                claims = int(str(row.get("Number of Claims", "0")).replace(",", ""))
                amount = float(str(row.get("Amount of Claims", "0")).replace(",", ""))
                vat_amount = float(str(row.get("Amount of Claims with VAT", "0")).replace(",", ""))
            except Exception as e:
                claims, amount, vat_amount = 0, 0.0, 0.0

            cleaned_row = {
                "Benefit Sama": benefit_name,
                "Number of Claims": claims,
                "Amount of Claims": amount,
                "Amount of Claims with VAT": vat_amount,
                "Notes": note,
                "Policy Year": "Last Policy Year",
            }
            cleaned_rows.append(cleaned_row)

        cleaned_df = pd.DataFrame(cleaned_rows)
        benefits_df = cleaned_df.reset_index(drop=True)

        
        end_date = meta_data.get("PolicyExpiryDate")
        if end_date:
            end_date = end_date.replace(",", "")
            try:
                end_date = pd.to_datetime(end_date, format="%b%d%Y").strftime("%Y-%m-%d")
            except:
                end_date = None

        overall_limit = meta_data.get("OverallBenefitLimit")
        if overall_limit:
            overall_limit = overall_limit.replace(",", "")

        benefits_df["End date"] = end_date
        benefits_df["Class"] = meta_data.get("Class")
        benefits_df["Overall Limit"] = overall_limit

        print(benefits_df)

        return benefits_df





if __name__ == "__main__":
    extractor = PDFExtractor(file_path="OCR Test Template (1) (1).pdf")
    tables = extractor.extract()
    extractor.preprocess_benefits_df(tables)
    
    
