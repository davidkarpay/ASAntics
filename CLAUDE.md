# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Streamlit web application** for managing State Attorney's Office (SAO) contact information. The application allows users to import contact data from PDF phone lists, search contacts, manage favorites, and export data.

### Key Components

- **sao_contact_manager.py** - Main Streamlit application (2215 lines) containing:
  - SQLite database management
  - PDF parsing with PyMuPDF
  - Multi-tab UI (Search, Favorites, All Contacts, Add Contact)
  - Contact search and filtering functionality
- **enhanced_pdf_parser.py** - Specialized PDF parser class for SAO phone lists (not currently integrated)
- **PDFs/** - Directory containing sample/test PDF data

## Development Commands

### Running the Application
```bash
streamlit run sao_contact_manager.py
```

### Installing Dependencies
```bash
pip install streamlit pandas pymupdf
```

### Database Location
- SQLite database: `sao_contacts.db` (created automatically)

## Architecture Notes

### Database Schema
- **contacts** table: Main contact information with fields for name, position, divisions, phone extension, department
- **favorites** table: User-saved favorite contacts with notes
- **recent_searches** table: Search history tracking

### PDF Processing
The application parses State Attorney's Office phone list PDFs using position-based text extraction. It identifies different divisions (County Court, Felony Trial, Juvenile) and extracts contact information accordingly.

### UI Structure
Streamlit tabs organize functionality:
1. **Search Tab** - Main search interface with division filters
2. **Favorites Tab** - Manage saved contacts
3. **All Contacts Tab** - Browse all contacts with export options
4. **Add Contact Tab** - Manual contact entry form

## Code Structure Issues

**Fixed:** The main file previously had significant code duplication and syntax errors. The file has been cleaned up from 2215 lines to 604 lines, removing duplicated functions and corrupted code sections. The application should now run without syntax errors.

When making changes:
- Look for similar functions before adding new ones  
- The enhanced PDF parser class exists but isn't integrated with the main application

### Key Functions (in sao_contact_manager.py)
- `init_database()` - Database initialization
- `parse_pdf_content()` - PDF text extraction and parsing
- `search_contacts()` - Database search functionality
- Various UI rendering functions for each tab

## Development Context

- Designed specifically for Palm Beach County SAO (hardcoded 561-355 phone prefix)
- No existing test suite or CI/CD configuration
- Missing standard Python project files (requirements.txt, setup.py, .gitignore)
- Application uses local SQLite storage for persistence