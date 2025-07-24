import fitz  # PyMuPDF
import pandas as pd
import re
from typing import List, Dict

class SAOPhoneListParser:
    """Specialized parser for State Attorney's Office phone list PDFs"""
    
    def __init__(self):
        self.column_headers = {
            'name': 'STATE ATTORNEY',
            'county_court': 'COUNTY COURT DIVISIONS',
            'felony_trial': 'FELONY TRIAL DIVISIONS',
            'intake': 'INTAKE',
            'juvenile': 'JUVENILE DIVISIONS',
            'admin': 'ADMINISTRATION'
        }
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """Parse the SAO phone list PDF with advanced table extraction"""
        doc = fitz.open(pdf_path)
        all_contacts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with positioning information
            blocks = page.get_text("dict")
            
            # Group text by vertical position (rows)
            rows = self._group_text_by_rows(blocks)
            
            # Process each row
            for row_data in rows:
                contact = self._parse_row(row_data)
                if contact and contact.get('name'):
                    all_contacts.append(contact)
        
        doc.close()
        return all_contacts
    
    def _group_text_by_rows(self, blocks) -> List[List[Dict]]:
        """Group text elements by their vertical position to form rows"""
        text_elements = []
        
        # Extract all text elements with positions
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_elements.append({
                                'text': text,
                                'x0': span["bbox"][0],
                                'y0': span["bbox"][1],
                                'x1': span["bbox"][2],
                                'y1': span["bbox"][3],
                                'font_size': span["size"]
                            })
        
        # Sort by vertical position
        text_elements.sort(key=lambda x: (x['y0'], x['x0']))
        
        # Group elements into rows (elements with similar y-coordinates)
        rows = []
        current_row = []
        current_y = None
        y_threshold = 5  # pixels
        
        for elem in text_elements:
            if current_y is None or abs(elem['y0'] - current_y) <= y_threshold:
                current_row.append(elem)
                if current_y is None:
                    current_y = elem['y0']
            else:
                if current_row:
                    rows.append(sorted(current_row, key=lambda x: x['x0']))
                current_row = [elem]
                current_y = elem['y0']
        
        if current_row:
            rows.append(sorted(current_row, key=lambda x: x['x0']))
        
        return rows
    
    def _parse_row(self, row_elements: List[Dict]) -> Dict:
        """Parse a single row of text elements into a contact record"""
        if not row_elements:
            return {}
        
        # Skip header rows
        row_text = ' '.join([elem['text'] for elem in row_elements])
        if any(header in row_text for header in ['STATE ATTORNEY', 'COUNTY COURT DIVISIONS', 'Updated']):
            return {}
        
        contact = {
            'name': '',
            'position': '',
            'county_court_divisions': '',
            'felony_trial_divisions': '',
            'intake': '',
            'juvenile_divisions': '',
            'phone_extension': '',
            'department': '',
            'administration': ''
        }
        
        # Analyze column positions based on x-coordinates
        # Typical column x-positions (approximate):
        # Name: 0-200
        # County Court: 200-300
        # Felony: 300-400
        # Intake: 400-500
        # Juvenile: 500-600
        # Extension: varies
        
        for elem in row_elements:
            text = elem['text']
            x_pos = elem['x0']
            
            # Name column (leftmost)
            if x_pos < 200 and re.match(r'^[A-Z][a-z]+', text):
                if not contact['name']:
                    contact['name'] = text
                elif not contact['position'] and not re.match(r'^\d{4}$', text):
                    contact['position'] = text
            
            # Phone extension (4-digit number)
            elif re.match(r'^\d{4}$', text):
                contact['phone_extension'] = text
            
            # Division assignments based on x-position and content
            elif 200 <= x_pos < 300:
                if any(marker in text for marker in ['CC', 'Div', 'Court']):
                    contact['county_court_divisions'] = text
            
            elif 300 <= x_pos < 400:
                if any(marker in text for marker in ['FEL', 'Felony', 'Div']):
                    contact['felony_trial_divisions'] = text
            
            elif 400 <= x_pos < 500:
                if 'Intake' in text or 'INTAKE' in text:
                    contact['intake'] = text
            
            elif 500 <= x_pos < 600:
                if 'Juvenile' in text or 'JUV' in text:
                    contact['juvenile_divisions'] = text
            
            # Administrative assignments
            elif any(admin in text for admin in ['Chief', 'Admin', 'Director', 'Manager']):
                contact['administration'] = text
        
        # Clean up the contact data
        contact = {k: v.strip() for k, v in contact.items() if v}
        
        return contact
    
    def parse_with_validation(self, pdf_path: str) -> pd.DataFrame:
        """Parse PDF and return as DataFrame for easy validation"""
        contacts = self.parse_pdf(pdf_path)
        df = pd.DataFrame(contacts)
        
        # Add validation flags
        df['has_name'] = df['name'].notna() & (df['name'] != '')
        df['has_extension'] = df['phone_extension'].notna() & (df['phone_extension'] != '')
        df['is_valid'] = df['has_name'] & df['has_extension']
        
        return df