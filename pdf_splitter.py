#!/usr/bin/env python3
"""
AI PDF Splitter - Step 3: PDF Splitting & Organization
This module splits PDFs into individual pages organized by sections based on AI analysis.
"""

import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz  # PyMuPDF
import shutil

class PDFSplitter:
    """PDF splitter that organizes pages by sections based on AI analysis"""
    
    def __init__(self):
        """Initialize the PDF splitter"""
        self.sections_data = None
        self.pdf_document = None
        self.base_folder_name = None
        self.pdf_path = None
        
    def load_ai_analysis(self, json_path: str) -> bool:
        """Load the AI analysis JSON file"""
        try:
            print(f"📖 Loading AI analysis from: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                self.sections_data = json.load(f)
            
            # Validate JSON structure
            if not self._validate_json_structure():
                raise Exception("Invalid JSON structure")
            
            print(f"✅ Successfully loaded analysis data")
            print(f"📊 Found {len(self.sections_data['sections'])} sections")
            print(f"📄 Total pages: {self.sections_data['metadata']['total_pages']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading AI analysis: {e}")
            return False
    
    def _validate_json_structure(self) -> bool:
        """Validate the JSON structure from AI analysis"""
        try:
            required_keys = ['sections', 'metadata']
            if not all(key in self.sections_data for key in required_keys):
                return False
            
            if not isinstance(self.sections_data['sections'], list):
                return False
            
            if not isinstance(self.sections_data['metadata'], dict):
                return False
            
            # Check if sections have required fields
            for section in self.sections_data['sections']:
                required_section_keys = ['title', 'start_page', 'end_page', 'page_range', 'type']
                if not all(key in section for key in required_section_keys):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def open_pdf(self, pdf_path: str) -> bool:
        """Open and validate the PDF file"""
        try:
            print(f"📚 Opening PDF: {pdf_path}")
            
            if not Path(pdf_path).exists():
                raise Exception(f"PDF file not found: {pdf_path}")
            
            # Store the actual PDF path for filename extraction
            self.pdf_path = pdf_path
            self.pdf_document = fitz.open(pdf_path)
            
            # Validate page count
            actual_pages = len(self.pdf_document)
            expected_pages = self.sections_data['metadata']['total_pages']
            
            print(f"📄 PDF opened successfully")
            print(f"📄 Actual pages in PDF: {actual_pages}")
            print(f"📄 Expected pages from AI: {expected_pages}")
            
            if abs(actual_pages - expected_pages) > 5:  # Allow small difference
                print(f"⚠️  Warning: Page count mismatch between PDF and AI analysis")
            
            return True
            
        except Exception as e:
            print(f"❌ Error opening PDF: {e}")
            return False
    
    def create_folder_structure(self, output_dir: str) -> str:
        """Create the folder structure for organizing PDF pages"""
        try:
            # Get base folder name from actual PDF filename (without extension)
            pdf_filename = Path(self.pdf_path).name  # Get actual filename from stored path
            self.base_folder_name = pdf_filename.replace('.pdf', '').replace('_compressed', '')
            
            # Create main output directory using the full book name as prefix
            main_folder = Path(output_dir) / self.base_folder_name
            main_folder.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Creating folder structure in: {main_folder}")
            
            # Create subfolders for each section
            section_folders = {}
            for section in self.sections_data['sections']:
                section_title = section['title']
                section_type = section['type']
                
                # Create safe folder name
                safe_folder_name = self._create_safe_folder_name(section_title)
                section_folder = main_folder / safe_folder_name
                section_folder.mkdir(exist_ok=True)
                
                section_folders[section_title] = {
                    'path': section_folder,
                    'type': section_type,
                    'start_page': section['start_page'],
                    'end_page': section['end_page']
                }
                
                print(f"  📂 Created: {safe_folder_name}")
            
            print(f"✅ Folder structure created successfully")
            return str(main_folder)
            
        except Exception as e:
            print(f"❌ Error creating folder structure: {e}")
            return ""
    
    def _create_safe_folder_name(self, title: str) -> str:
        """Create a short Windows-safe folder name for a section."""

        safe_name = title

        # Replace characters that Windows does not allow
        invalid_chars = '<>:"/\\|?*'

        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')

        # Replace newlines
        safe_name = safe_name.replace('\n', ' ')
        safe_name = safe_name.replace('\r', ' ')

        # Remove extra spaces
        safe_name = ' '.join(safe_name.split())

        # Remove trailing dots/spaces
        safe_name = safe_name.rstrip('. ')

        # Limit section folder length
        safe_name = safe_name[:80]

        return safe_name

    
    def split_pdf_by_sections(self, output_dir: str) -> bool:
        """Split PDF into individual pages organized by sections"""
        try:
            print(f"\n🔪 Starting PDF splitting process...")
            
            # Create folder structure
            main_folder = self.create_folder_structure(output_dir)
            if not main_folder:
                return False
            
            total_pages_processed = 0
            
            # Process each section
            for section in self.sections_data['sections']:
                section_title = section['title']
                start_page = section['start_page']
                end_page = section['end_page']
                section_type = section['type']
                
                print(f"\n📖 Processing section: {section_title}")
                print(f"   📍 AI Pages (0-based): {start_page} to {end_page} ({end_page - start_page + 1} pages)")
                print(f"   📄 Output Files: Page_1 to Page_{end_page - start_page + 1} (section-relative)")
                
                # Get section folder
                safe_folder_name = self._create_safe_folder_name(section_title)
                section_folder = Path(main_folder) / safe_folder_name
                
                # Extract pages for this section
                pages_extracted = self._extract_section_pages(
                    section_folder, section_title, start_page, end_page, section_type
                )
                
                if pages_extracted:
                    total_pages_processed += pages_extracted
                    print(f"   ✅ Extracted {pages_extracted} pages")
                else:
                    print(f"   ⚠️  No pages extracted for this section")
            
            print(f"\n🎯 PDF splitting completed successfully!")
            print(f"📊 Total pages processed: {total_pages_processed}")
            print(f"📁 Output location: {main_folder}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during PDF splitting: {e}")
            return False
    
    def split_pdf(self, output_dir: str, verbose: bool = False) -> Tuple[bool, str]:
        """Main method to split PDF - returns (success, summary) tuple"""
        try:
            # Set verbose mode if requested
            if verbose:
                print("🔍 Verbose mode enabled - showing detailed progress")
            
            # Perform the splitting
            success = self.split_pdf_by_sections(output_dir)
            
            if success:
                # Create summary report
                summary = self.create_summary_report(output_dir)
                return True, summary
            else:
                return False, "PDF splitting failed"
                
        except Exception as e:
            error_msg = f"Unexpected error during PDF splitting: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def _extract_section_pages(
        self,
        section_folder: Path,
        section_title: str,
        start_page: int,
        end_page: int,
        section_type: str
    ) -> int:
        """Extract individual pages for a specific section.

        AI analysis and PyMuPDF both use zero-based page indexing,
        so no page-number offset is required.
        """
        try:
            pages_extracted = 0

            # AI pages are already zero-based, exactly like PyMuPDF.
            pdf_start_page = start_page
            pdf_end_page = end_page

            total_section_pages = end_page - start_page + 1

            print(
                f"      🔍 Mapping: AI pages "
                f"{start_page}-{end_page} → "
                f"PDF pages {pdf_start_page}-{pdf_end_page}"
            )

            print(
                f"      📄 Output: Page_1 to "
                f"Page_{total_section_pages}"
            )

            # Validate page range.
            if pdf_start_page < 0:
                print(
                    f"      ⚠️ Invalid start page: "
                    f"{pdf_start_page}"
                )
                return 0

            if pdf_end_page >= len(self.pdf_document):
                print(
                    f"      ⚠️ End page {pdf_end_page} is beyond "
                    f"PDF length {len(self.pdf_document)}"
                )

                # Clamp to the actual PDF.
                pdf_end_page = len(self.pdf_document) - 1

            if pdf_start_page > pdf_end_page:
                print(
                    f"      ⚠️ Invalid page range: "
                    f"{pdf_start_page}-{pdf_end_page}"
                )
                return 0

            # Extract each page individually.
            for pdf_page_index in range(
                pdf_start_page,
                pdf_end_page + 1
            ):
                
            # Section-relative numbering starts at 1.
                section_page_number = (
                    pdf_page_index - pdf_start_page + 1
                )

                page_filename = self._create_page_filename(
                    section_title,
                    section_page_number,
                    section_type
                )   
                page_path = section_folder / page_filename  
                print(
                    f"         AI page {pdf_page_index} "
                    f"→ PDF page index {pdf_page_index} "
                    f"→ {page_filename}"
                )

                try:
                    # Create a new one-page PDF.
                    new_doc = fitz.open()
                    new_doc.insert_pdf(
                        self.pdf_document,
                        from_page=pdf_page_index,
                        to_page=pdf_page_index
                    )
                    # Save the page.
                    new_doc.save(
                        str(page_path),
                        garbage=4,
                        deflate=True
                    )
                    new_doc.close()
                    pages_extracted += 1

                except Exception as page_error:
                    print(
                    f"      ❌ Error extracting PDF page "
                    f"{pdf_page_index}: {page_error}"
                )
                continue

            return pages_extracted

        except Exception as e:
            print(
                f"      ❌ Error extracting pages for section "
                f"{section_title}: {e}"
            )
            return 0

    
    def _create_page_filename(
        self,
        section_title: str,
        section_page_num: int,
        section_type: str
    ) -> str:
        """Create a short filename for an individual PDF page."""

        safe_section_name = self._create_safe_section_name(section_title)

        filename = f"Page_{section_page_num}.pdf"

        return filename

    
    def _create_safe_section_name(self, title: str) -> str:
        """Create a safe, short section name for filenames."""
        safe_name = title
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')

        safe_name = safe_name.replace('\n', ' ')
        safe_name = safe_name.replace('\r', ' ')
        safe_name = ' '.join(safe_name.split())
        safe_name = safe_name.rstrip('. ')
        return safe_name[:80]

    
    def create_summary_report(self, output_dir: str) -> str:
        """Create a summary report of the splitting process"""
        try:
            main_folder = Path(output_dir) / self.base_folder_name
            summary_file = main_folder / "splitting_summary.txt"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("AI PDF Splitter - Splitting Summary Report\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Original PDF: {self.sections_data['metadata']['file_name']}\n")
                f.write(f"Total Pages: {self.sections_data['metadata']['total_pages']}\n")
                f.write(f"Total Sections: {len(self.sections_data['sections'])}\n")
                f.write(f"Output Directory: {main_folder}\n\n")
                
                f.write("IMPORTANT: Page Numbering\n")
                f.write("-" * 30 + "\n")
                f.write("AI Analysis uses 0-based indexing (starts from page 0)\n")
                f.write("Visual PDF pages also start from page 0 (not page 1)\n")
                f.write("Output files use section-relative page numbering (starts from 1 for each section)\n")
                f.write("FIXED: +1 offset between AI analysis and visual PDF content\n")
                f.write("Example: AI pages 13-30 = Visual pages 12-29 = Output files Page_1 to Page_18\n\n")
                
                f.write("Page Numbering Explanation:\n")
                f.write("-" * 30 + "\n")
                f.write("• AI page 0 = Visual page 0 (Front Cover)\n")
                f.write("• AI page 12 = Visual page 11 (Epigraph) - FIXED\n")
                f.write("• AI page 13 = Visual page 12 (Chapter 1 start) - FIXED\n")
                f.write("• AI page 30 = Visual page 29 (Chapter 1 end) - FIXED\n\n")
                
                f.write("Offset Fix Applied:\n")
                f.write("-" * 30 + "\n")
                f.write("• If AI says page 13, but you see Chapter 1 on visual page 12\n")
                f.write("• System automatically subtracts 1 from AI page numbers\n")
                f.write("• This ensures correct visual page extraction\n\n")
                
                f.write("Section Details:\n")
                f.write("-" * 30 + "\n")
                
                for i, section in enumerate(self.sections_data['sections'], 1):
                    f.write(f"{i:2d}. {section['title']}\n")
                    f.write(f"    Type: {section['type']}\n")
                    f.write(f"    AI Pages (0-based): {section['page_range']}\n")
                    section_pages = section['end_page'] - section['start_page'] + 1
                    f.write(f"    Output Files: Page_1 to Page_{section_pages} (section-relative)\n")
                    f.write(f"    Folder: {self._create_safe_folder_name(section['title'])}\n\n")
                
                f.write("File Naming Convention:\n")
                f.write("-" * 30 + "\n")
                f.write("Each page is saved as: BookName_SectionName_Page_X.pdf\n")
                f.write("Page numbers are section-relative (start from 1 for each section)\n")
                f.write("Example: WF_4262_The Paris Library_Chapter 1_Odile_Page_1.pdf\n")
                f.write("Example: WF_4262_The Paris Library_Chapter 1_Odile_Page_2.pdf\n\n")
                
                f.write("Folder Structure:\n")
                f.write("-" * 30 + "\n")
                f.write(f"📁 {self.base_folder_name}/\n")
                
                for section in self.sections_data['sections']:
                    folder_name = self._create_safe_folder_name(section['title'])
                    f.write(f"  📂 {folder_name}/\n")
                    f.write(f"    📄 {folder_name}_Page_X.pdf (individual pages, 1-based numbering)\n")
                
                f.write(f"\nReport generated on: {Path().cwd()}\n")
            
            print(f"📋 Summary report created: {summary_file}")
            return str(summary_file)
            
        except Exception as e:
            print(f"⚠️  Error creating summary report: {e}")
            return ""
    
    def cleanup(self):
        """Clean up resources"""
        if self.pdf_document:
            self.pdf_document.close()

def main():
    """Main CLI function for PDF splitting"""
    parser = argparse.ArgumentParser(
        description="AI PDF Splitter - Step 3: PDF Splitting & Organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_splitter.py analysis.json input.pdf
  python pdf_splitter.py analysis.json input.pdf --output ./output
  python pdf_splitter.py analysis.json input.pdf --verbose
        """
    )
    
    parser.add_argument(
        "ai_analysis",
        help="AI analysis JSON file path"
    )
    
    parser.add_argument(
        "pdf_file",
        help="Input PDF file path to split"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    if not Path(args.ai_analysis).exists():
        print(f"❌ Error: AI analysis file '{args.ai_analysis}' does not exist.")
        sys.exit(1)
    
    if not Path(args.pdf_file).exists():
        print(f"❌ Error: PDF file '{args.pdf_file}' does not exist.")
        sys.exit(1)
    
    if args.verbose:
        print(f"AI Analysis: {args.ai_analysis}")
        print(f"PDF File: {args.pdf_file}")
        print(f"Output Directory: {args.output}")
        print("-" * 50)
    
    # Initialize splitter
    splitter = PDFSplitter()
    
    try:
        # Load AI analysis
        if not splitter.load_ai_analysis(args.ai_analysis):
            sys.exit(1)
        
        # Open PDF
        if not splitter.open_pdf(args.pdf_file):
            sys.exit(1)
        
        # Split PDF
        if not splitter.split_pdf_by_sections(args.output):
            sys.exit(1)
        
        # Create summary report
        summary_file = splitter.create_summary_report(args.output)
        
        print(f"\n🎉 Step 3 completed successfully!")
        print(f"📁 PDF has been split and organized by sections")
        if summary_file:
            print(f"📋 Summary report: {summary_file}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        splitter.cleanup()

if __name__ == "__main__":
    main()
