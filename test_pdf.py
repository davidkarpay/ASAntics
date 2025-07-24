#!/usr/bin/env python3
import fitz
import os

try:
    # Check if PDF exists
    pdf_path = 'PDFs/June_2025.pdf'
    if not os.path.exists(pdf_path):
        print(f"PDF not found at {pdf_path}")
        print("Available files:")
        for f in os.listdir('PDFs'):
            print(f"  - {f}")
        exit(1)
    
    # Open PDF
    doc = fitz.open(pdf_path)
    print(f"PDF opened successfully, has {len(doc)} pages")
    
    if len(doc) > 0:
        page = doc[0]
        text = page.get_text()
        print(f"First page has {len(text)} characters")
        print("First 200 characters:")
        print(repr(text[:200]))
        print("\n" + "="*50 + "\n")
        
        # Try the enhanced parser
        from enhanced_pdf_parser import SAOPhoneListParser
        parser = SAOPhoneListParser()
        contacts = parser.parse_pdf(pdf_path)
        print(f"Enhanced parser found {len(contacts)} contacts")
        
        if contacts:
            print("First contact:", contacts[0])
        else:
            print("No contacts found - let's debug the parsing...")
            # Get structured text
            blocks = page.get_text("dict")
            print(f"Found {len(blocks.get('blocks', []))} text blocks")
            
            # Show some raw text elements
            for i, block in enumerate(blocks.get('blocks', [])[:3]):
                if 'lines' in block:
                    print(f"Block {i} lines:")
                    for line in block['lines'][:2]:
                        for span in line['spans']:
                            text_content = span['text'].strip()
                            if text_content:
                                print(f"  Text: '{text_content}' at position {span['bbox']}")
    
    doc.close()
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
