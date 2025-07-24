import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import fitz  # PyMuPDF
import re
from pathlib import Path
from enhanced_pdf_parser import SAOPhoneListParser
from auth_ui import require_authentication
from auth_system import AuthSystem
from admin_ui import show_admin_panel

# Page config
st.set_page_config(
    page_title="SAO Contact Manager",
    page_icon="⚖️",
    layout="wide"
)

# Database setup
DB_PATH = "sao_contacts.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position TEXT,
            county_court_divisions TEXT,
            felony_trial_divisions TEXT,
            intake TEXT,
            juvenile_divisions TEXT,
            phone_extension TEXT,
            administration TEXT,
            department TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pdf_source TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_name TEXT,
            contact_extension TEXT,
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(contact_name, contact_extension)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recent_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term TEXT,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_name ON contacts(name);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_division ON contacts(county_court_divisions);
    """)
    
    # Authentication tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            verification_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pin_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            verification_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_pins_user_id ON login_pins(user_id);
    """)
    
    # Add admin column to existing users table if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    conn.commit()
    conn.close()

def parse_csv_data(csv_path):
    """Parse the SAO phone list CSV file"""
    import csv
    
    contacts = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as file:
            # Read the CSV content
            content = file.read()
            
            # Split into lines and process each line
            lines = content.split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Parse CSV line manually to handle the complex format
                fields = []
                current_field = ""
                in_quotes = False
                
                i = 0
                while i < len(line):
                    char = line[i]
                    
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        fields.append(current_field.strip())
                        current_field = ""
                    else:
                        current_field += char
                    i += 1
                
                # Add the last field
                if current_field:
                    fields.append(current_field.strip())
                
                # Process fields to extract contacts
                # The CSV has multiple contacts per row, separated by commas
                i = 0
                while i < len(fields):
                    field = fields[i].strip()
                    
                    # Skip empty fields and single letters (section dividers)
                    if not field or len(field) <= 1:
                        i += 1
                        continue
                    
                    # Check if this looks like a name (has comma and letters)
                    if ',' in field and not field.startswith('(') and not field.isdigit():
                        name = field.strip('"')
                        
                        # Skip obvious non-names
                        if any(skip in name.upper() for skip in ['UPDATED', 'STATE ATTORNEY', 'COUNTY COURT']):
                            i += 1
                            continue
                        
                        # Initialize contact record
                        contact = {
                            'name': name,
                            'position': '',
                            'county_court_divisions': '',
                            'felony_trial_divisions': '',
                            'intake': '',
                            'juvenile_divisions': '',
                            'phone_extension': '',
                            'administration': '',
                            'department': ''
                        }
                        
                        # Look for phone extension in next field
                        if i + 1 < len(fields):
                            next_field = fields[i + 1].strip()
                            if re.match(r'^\d{4}$', next_field):
                                contact['phone_extension'] = next_field
                                i += 1  # Skip the extension field
                        
                        # Look for division/department info in next field
                        if i + 1 < len(fields):
                            next_field = fields[i + 1].strip()
                            if next_field.startswith('(') and next_field.endswith(')'):
                                dept_info = next_field.strip('()')
                                
                                # Categorize the department information
                                dept_lower = dept_info.lower()
                                if any(term in dept_lower for term in ['cc', 'county court']):
                                    contact['county_court_divisions'] = dept_info
                                elif any(term in dept_lower for term in ['fel', 'felony']):
                                    contact['felony_trial_divisions'] = dept_info
                                elif any(term in dept_lower for term in ['juv', 'juvenile']):
                                    contact['juvenile_divisions'] = dept_info
                                elif 'intake' in dept_lower:
                                    contact['intake'] = dept_info
                                elif any(term in dept_lower for term in ['admin', 'legal', 'info tech', 'investigation']):
                                    contact['administration'] = dept_info
                                else:
                                    contact['department'] = dept_info
                                
                                i += 1  # Skip the department field
                        
                        # Only add contacts with both name and extension
                        if contact['name'] and contact['phone_extension']:
                            contacts.append(contact)
                    
                    i += 1
        
        return contacts
        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return []

def parse_pdf_table(pdf_path):
    """Parse the SAO phone list - now supports both PDF and CSV"""
    file_ext = os.path.splitext(pdf_path)[1].lower()
    
    if file_ext == '.csv':
        return parse_csv_data(pdf_path)
    elif file_ext == '.pdf':
        # Keep existing PDF parsing as fallback
        try:
            parser = SAOPhoneListParser()
            contacts = parser.parse_pdf(pdf_path)
            
            # Convert to the expected format for compatibility
            formatted_contacts = []
            for contact in contacts:
                formatted_contact = {
                    'name': contact.get('name', ''),
                    'position': contact.get('position', ''),
                    'county_court_divisions': contact.get('county_court_divisions', ''),
                    'felony_trial_divisions': contact.get('felony_trial_divisions', ''),
                    'intake': contact.get('intake', ''),
                    'juvenile_divisions': contact.get('juvenile_divisions', ''),
                    'phone_extension': contact.get('phone_extension', ''),
                    'administration': contact.get('administration', ''),
                    'department': contact.get('department', '')
                }
                # Only add contacts with at least a name
                if formatted_contact['name']:
                    formatted_contacts.append(formatted_contact)
            
            return formatted_contacts
            
        except Exception as e:
            # Fallback to simpler text extraction if enhanced parser fails
            return parse_pdf_simple(pdf_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

def parse_pdf_simple(pdf_path):
    """Simple fallback PDF parser"""
    doc = fitz.open(pdf_path)
    all_data = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text
        text = page.get_text("dict")
        blocks = text.get("blocks", [])
        
        current_record = {}
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_content = span["text"].strip()
                        
                        if not text_content:
                            continue
                        
                        # Detect names (usually larger font or bold)
                        if re.match(r'^[A-Z][a-z]+,?\s+[A-Z]', text_content) and len(text_content) > 5:
                            # Skip header-like text
                            if any(header in text_content.upper() for header in ['STATE ATTORNEY', 'COUNTY COURT', 'DIVISIONS', 'UPDATED']):
                                continue
                                
                            if current_record and current_record.get('name'):
                                all_data.append(current_record)
                            
                            current_record = {
                                'name': text_content,
                                'position': '',
                                'county_court_divisions': '',
                                'felony_trial_divisions': '',
                                'intake': '',
                                'juvenile_divisions': '',
                                'phone_extension': '',
                                'administration': '',
                                'department': ''
                            }
                        
                        # Extract phone extensions
                        elif re.match(r'^\d{4}$', text_content):
                            if current_record:
                                current_record['phone_extension'] = text_content
                        
                        # Extract division information
                        elif current_record:
                            text_lower = text_content.lower()
                            if 'county' in text_lower or 'cc' in text_lower:
                                current_record['county_court_divisions'] = text_content
                            elif 'felony' in text_lower or 'fel' in text_lower:
                                current_record['felony_trial_divisions'] = text_content
                            elif 'juvenile' in text_lower or 'juv' in text_lower:
                                current_record['juvenile_divisions'] = text_content
                            elif 'intake' in text_lower:
                                current_record['intake'] = text_content
                            elif 'admin' in text_lower:
                                current_record['administration'] = text_content
        
        # Don't forget to add the last record
        if current_record and current_record.get('name'):
            all_data.append(current_record)
    
    doc.close()
    return all_data

def parse_csv_content(csv_path):
    """Parse CSV file and extract contact information"""
    contacts = []
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path, header=None)
        
        for _, row in df.iterrows():
            # Skip empty rows
            if row.isna().all():
                continue
                
            # Process each row - contacts are in groups of 4 columns (name, ext, division, empty)
            row_values = row.values
            i = 0
            while i < len(row_values):
                # Look for contact patterns: "Last, First", extension, (division)
                if pd.notna(row_values[i]) and isinstance(row_values[i], str):
                    contact_text = str(row_values[i]).strip()
                    
                    # Skip empty cells and separators
                    if not contact_text or contact_text in ['', ',', ' ']:
                        i += 1
                        continue
                    
                    # Check if this looks like a name (contains comma)
                    if ',' in contact_text and not contact_text.startswith('('):
                        name = contact_text.strip('"')
                        extension = ''
                        division = ''
                        
                        # Look for extension in next cell
                        if i + 1 < len(row_values) and pd.notna(row_values[i + 1]):
                            ext_text = str(row_values[i + 1]).strip()
                            if ext_text.isdigit() or '-' in ext_text:
                                extension = ext_text
                        
                        # Look for division in next cell (usually in parentheses)
                        if i + 2 < len(row_values) and pd.notna(row_values[i + 2]):
                            div_text = str(row_values[i + 2]).strip()
                            if div_text.startswith('(') and div_text.endswith(')'):
                                division = div_text.strip('()')
                        
                        # Only add if we have a valid name
                        if name and len(name) > 3:
                            contacts.append({
                                'name': name,
                                'position': '',
                                'county_court_divisions': division if 'cc' in division.lower() or 'county' in division.lower() else '',
                                'felony_trial_divisions': division if 'fel' in division.lower() else '',
                                'intake': division if 'intake' in division.lower() else '',
                                'juvenile_divisions': division if 'juv' in division.lower() else '',
                                'phone_extension': extension,
                                'administration': division if 'admin' in division.lower() else '',
                                'department': division
                            })
                        
                        # Skip ahead by 3-4 cells to next potential contact
                        i += 4
                    else:
                        i += 1
                else:
                    i += 1
        
        return contacts
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return []

def save_to_database(data, pdf_source):
    """Save parsed data to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing data from this source
    cursor.execute("DELETE FROM contacts WHERE pdf_source = ?", (pdf_source,))
    
    # Insert new data
    for record in data:
        cursor.execute("""
            INSERT INTO contacts (
                name, position, county_court_divisions, felony_trial_divisions,
                intake, juvenile_divisions, phone_extension, administration,
                department, pdf_source, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('name', ''),
            record.get('position', ''),
            record.get('county_court_divisions', ''),
            record.get('felony_trial_divisions', ''),
            record.get('intake', ''),
            record.get('juvenile_divisions', ''),
            record.get('phone_extension', ''),
            record.get('administration', ''),
            record.get('department', ''),
            pdf_source,
            datetime.now()
        ))
    
    conn.commit()
    conn.close()

def add_to_favorites(name, extension, notes=""):
    """Add contact to favorites"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO favorites (contact_name, contact_extension, notes)
            VALUES (?, ?, ?)
        """, (name, extension, notes))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding to favorites: {str(e)}")
        return False
    finally:
        conn.close()

def remove_from_favorites(name, extension):
    """Remove contact from favorites"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM favorites WHERE contact_name = ? AND contact_extension = ?
    """, (name, extension))
    conn.commit()
    conn.close()

def get_favorites():
    """Get all favorite contacts"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT f.contact_name, f.contact_extension, f.notes, f.added_at,
               c.position, c.county_court_divisions, c.felony_trial_divisions, 
               c.juvenile_divisions, c.department
        FROM favorites f
        LEFT JOIN contacts c ON f.contact_name = c.name AND f.contact_extension = c.phone_extension
        ORDER BY f.added_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def search_contacts(search_term="", division_filter=""):
    """Search contacts in database"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT DISTINCT name, position, county_court_divisions, felony_trial_divisions,
               intake, juvenile_divisions, phone_extension, department
        FROM contacts
        WHERE 1=1
    """
    params = []
    
    if search_term:
        query += """ AND (
            name LIKE ? OR 
            position LIKE ? OR 
            department LIKE ? OR
            phone_extension LIKE ?
        )"""
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern] * 4)
    
    if division_filter and division_filter != "All":
        query += """ AND (
            county_court_divisions LIKE ? OR 
            felony_trial_divisions LIKE ? OR
            juvenile_divisions LIKE ?
        )"""
        division_pattern = f"%{division_filter}%"
        params.extend([division_pattern] * 3)
    
    query += " ORDER BY name"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def get_all_divisions():
    """Get list of all unique divisions"""
    conn = sqlite3.connect(DB_PATH)
    
    divisions = set(['All'])
    
    # Get county court divisions
    df = pd.read_sql_query(
        "SELECT DISTINCT county_court_divisions FROM contacts WHERE county_court_divisions != ''", 
        conn
    )
    divisions.update(df['county_court_divisions'].tolist())
    
    # Get felony divisions
    df = pd.read_sql_query(
        "SELECT DISTINCT felony_trial_divisions FROM contacts WHERE felony_trial_divisions != ''", 
        conn
    )
    divisions.update(df['felony_trial_divisions'].tolist())
    
    conn.close()
    return sorted(list(divisions))

# Initialize database
init_database()

# Check authentication before showing main UI
if not require_authentication():
    st.stop()

# Main UI
st.title("⚖️ State Attorney's Office Contact Manager")
st.markdown("Search and manage contact information for the State Attorney's Office")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Update Database")
    
    uploaded_file = st.file_uploader(
        "Upload new phone list (PDF or CSV)",
        type=['pdf', 'csv'],
        help="Upload the latest SAO phone list PDF or CSV file to update the database"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        col1, col2 = st.columns(2)
        with col1:
            parse_button = st.button("Parse File", type="primary", use_container_width=True)
        with col2:
            if os.path.exists(temp_path):
                clear_button = st.button("Clear", type="secondary", use_container_width=True)
                if clear_button:
                    os.remove(temp_path)
                    st.rerun()
        
        if parse_button:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            spinner_text = f"Parsing {file_extension.upper()}..."
            
            with st.spinner(spinner_text):
                try:
                    # Parse based on file type
                    if file_extension == 'csv':
                        data = parse_csv_content(temp_path)
                    else:  # PDF
                        data = parse_pdf_table(temp_path)
                    
                    st.session_state['parsed_data'] = data
                    st.session_state['pdf_source'] = uploaded_file.name
                    st.success(f"✅ Parsed {len(data)} potential contacts!")
                    
                except Exception as e:
                    st.error(f"Error parsing {file_extension.upper()}: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        
        # Show parsed data preview
        if 'parsed_data' in st.session_state and st.session_state['parsed_data']:
            st.divider()
            st.subheader("📋 Preview Parsed Data")
            
            # Show first few records
            preview_data = st.session_state['parsed_data'][:5]
            for i, record in enumerate(preview_data):
                with st.expander(f"Contact {i+1}: {record.get('name', 'Unknown')}"):
                    for key, value in record.items():
                        if value:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
            if len(st.session_state['parsed_data']) > 5:
                st.info(f"... and {len(st.session_state['parsed_data']) - 5} more contacts")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save to Database", type="primary", use_container_width=True):
                    save_to_database(st.session_state['parsed_data'], st.session_state['pdf_source'])
                    st.success("✅ Saved to database!")
                    
                    # Clean up
                    del st.session_state['parsed_data']
                    del st.session_state['pdf_source']
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", type="secondary", use_container_width=True):
                    del st.session_state['parsed_data']
                    del st.session_state['pdf_source']
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    st.rerun()
    
    st.divider()
    
    # Database stats
    conn = sqlite3.connect(DB_PATH)
    total_contacts = pd.read_sql_query("SELECT COUNT(DISTINCT name) as count FROM contacts", conn).iloc[0]['count']
    last_update = pd.read_sql_query("SELECT MAX(updated_at) as last FROM contacts", conn).iloc[0]['last']
    conn.close()
    
    st.metric("Total Contacts", total_contacts)
    if last_update:
        st.metric("Last Updated", pd.to_datetime(last_update).strftime("%Y-%m-%d %H:%M"))

# Main content area - add admin tab for admin users
auth = AuthSystem()
current_user = auth.get_current_user()
is_admin = current_user and current_user.get('is_admin', False)

if is_admin:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Search", "⭐ Favorites", "📊 All Contacts", "➕ Add Contact", "👑 Admin"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "⭐ Favorites", "📊 All Contacts", "➕ Add Contact"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input(
            "Search by name, position, department, or phone extension",
            placeholder="e.g., Smith, 7234, County Court"
        )
    
    with col2:
        divisions = get_all_divisions()
        division_filter = st.selectbox(
            "Filter by Division",
            options=divisions,
            index=0
        )
    
    # Search results
    if search_term or division_filter != "All":
        results = search_contacts(search_term, division_filter)
        
        if not results.empty:
            st.subheader(f"Found {len(results)} contacts")
            
            # Create a more structured display
            for idx, row in results.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"### {row['name']}")
                        if row['position']:
                            st.caption(row['position'])
                    
                    with col2:
                        if row['phone_extension']:
                            st.metric("Extension", row['phone_extension'])
                    
                    with col3:
                        if row['phone_extension']:
                            # Create phone number with main office number
                            main_number = "(561) 355-"  # Palm Beach County SAO main
                            full_number = f"{main_number}{row['phone_extension']}"
                            st.markdown(f"📞 [{full_number}](tel:+15613550000,{row['phone_extension']})")
                    
                    with col4:
                        # Add to favorites button
                        fav_key = f"fav_{row['name']}_{row['phone_extension']}"
                        if st.button("⭐", key=fav_key, help="Add to favorites"):
                            if add_to_favorites(row['name'], row['phone_extension']):
                                st.success("Added to favorites!")
                                st.rerun()
                    
                    # Division details
                    division_cols = st.columns(4)
                    with division_cols[0]:
                        if row['county_court_divisions']:
                            st.write(f"**County Court:** {row['county_court_divisions']}")
                    with division_cols[1]:
                        if row['felony_trial_divisions']:
                            st.write(f"**Felony Trial:** {row['felony_trial_divisions']}")
                    with division_cols[2]:
                        if row['juvenile_divisions']:
                            st.write(f"**Juvenile:** {row['juvenile_divisions']}")
                    with division_cols[3]:
                        if row['intake']:
                            st.write(f"**Intake:** {row['intake']}")
                    
                    st.divider()
        else:
            st.info("No contacts found matching your search criteria")

with tab2:
    st.header("⭐ Favorite Contacts")
    
    favorites = get_favorites()
    
    if not favorites.empty:
        st.caption(f"You have {len(favorites)} favorite contacts")
        
        for idx, fav in favorites.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {fav['contact_name']}")
                    if fav['position']:
                        st.caption(fav['position'])
                    if fav['notes']:
                        st.info(f"📝 Note: {fav['notes']}")
                
                with col2:
                    st.metric("Extension", fav['contact_extension'])
                
                with col3:
                    # Quick dial
                    main_number = "(561) 355-"
                    full_number = f"{main_number}{fav['contact_extension']}"
                    st.markdown(f"📞 [{full_number}](tel:+15613550000,{fav['contact_extension']})")
                
                with col4:
                    if st.button("❌", key=f"remove_{idx}", help="Remove from favorites"):
                        remove_from_favorites(fav['contact_name'], fav['contact_extension'])
                        st.rerun()
                
                # Division info if available
                division_info = []
                if fav['county_court_divisions']:
                    division_info.append(f"**County:** {fav['county_court_divisions']}")
                if fav['felony_trial_divisions']:
                    division_info.append(f"**Felony:** {fav['felony_trial_divisions']}")
                if fav['juvenile_divisions']:
                    division_info.append(f"**Juvenile:** {fav['juvenile_divisions']}")
                
                if division_info:
                    st.write(" | ".join(division_info))
                
                st.divider()
        
        # Add notes to favorites
        st.subheader("Add Notes to Favorite")
        fav_names = favorites['contact_name'].tolist()
        selected_fav = st.selectbox("Select contact", fav_names)
        
        if selected_fav:
            note_text = st.text_area("Add/Update note", key="fav_note")
            if st.button("Save Note"):
                fav_row = favorites[favorites['contact_name'] == selected_fav].iloc[0]
                if add_to_favorites(selected_fav, fav_row['contact_extension'], note_text):
                    st.success("Note updated!")
                    st.rerun()
    else:
        st.info("No favorite contacts yet. Use the ⭐ button in search results to add favorites.")

with tab3:
    # Show all contacts
    all_contacts = search_contacts()
    
    if not all_contacts.empty:
        st.subheader(f"All Contacts ({len(all_contacts)} total)")
        
        # Add download button
        csv = all_contacts.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"sao_contacts_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Display as dataframe with search
        st.dataframe(
            all_contacts,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("Name", width="medium"),
                "position": st.column_config.TextColumn("Position", width="medium"),
                "county_court_divisions": st.column_config.TextColumn("County Court", width="small"),
                "felony_trial_divisions": st.column_config.TextColumn("Felony Trial", width="small"),
                "juvenile_divisions": st.column_config.TextColumn("Juvenile", width="small"),
                "phone_extension": st.column_config.TextColumn("Ext", width="small"),
                "department": st.column_config.TextColumn("Department", width="medium")
            }
        )
    else:
        st.info("No contacts in database. Please upload a PDF to get started.")

with tab3:
    st.subheader("Add New Contact")
    
    with st.form("add_contact_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*", placeholder="Last, First")
            position = st.text_input("Position/Title", placeholder="e.g., Assistant State Attorney")
            department = st.text_input("Department", placeholder="e.g., Felony Division")
            phone_extension = st.text_input("Phone Extension*", placeholder="4-digit extension (e.g., 7234)")
        
        with col2:
            county_court = st.text_input("County Court Division", placeholder="e.g., CC DIV B")
            felony_trial = st.text_input("Felony Trial Division", placeholder="e.g., FEL DIV 2")
            juvenile = st.text_input("Juvenile Division", placeholder="e.g., Juvenile Div A")
            intake = st.text_input("Intake", placeholder="e.g., Intake Unit")
        
        submitted = st.form_submit_button("Add Contact", type="primary", use_container_width=True)
        
        if submitted:
            if name and phone_extension:
                # Validate phone extension
                if not re.match(r'^\d{4}$', phone_extension):
                    st.error("Phone extension must be a 4-digit number")
                else:
                    # Add to database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute("""
                            INSERT INTO contacts (
                                name, position, county_court_divisions, felony_trial_divisions,
                                intake, juvenile_divisions, phone_extension, administration,
                                department, pdf_source, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name, position, county_court, felony_trial,
                            intake, juvenile, phone_extension, '',
                            department, 'Manual Entry', datetime.now()
                        ))
                        conn.commit()
                        st.success(f"✅ Successfully added {name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding contact: {str(e)}")
                    finally:
                        conn.close()
            else:
                st.error("Please fill in required fields (Name and Phone Extension)")

# Admin tab (only shown to admins)
if is_admin:
    with tab5:
        show_admin_panel()

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        SAO Contact Manager | Designed for efficient access to State Attorney's Office contacts
    </div>
    """,
    unsafe_allow_html=True
)
