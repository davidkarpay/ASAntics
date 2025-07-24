#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from sao_contact_manager import parse_csv_data

# Test the CSV parser
csv_path = r"c:\Users\Dkarpay\Downloads\Copy of June  2025-ALPHA.csv"

if os.path.exists(csv_path):
    print(f"Testing CSV parser with: {csv_path}")
    contacts = parse_csv_data(csv_path)
    print(f"Found {len(contacts)} contacts")
    
    if contacts:
        print("\nFirst 5 contacts:")
        for i, contact in enumerate(contacts[:5]):
            print(f"\n{i+1}. {contact['name']}")
            print(f"   Extension: {contact['phone_extension']}")
            print(f"   Department: {contact.get('department') or contact.get('county_court_divisions') or contact.get('felony_trial_divisions') or contact.get('juvenile_divisions') or contact.get('intake') or contact.get('administration') or 'N/A'}")
    else:
        print("No contacts found")
else:
    print(f"CSV file not found at: {csv_path}")
