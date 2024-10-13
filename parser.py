import argparse
import os
import fitz

def find_page_with_text(reader, search_text):
    """
    Search for a page that contains the specified text.
    Returns the page number if found, otherwise -1.
    """
    for page_num in range(len(reader)):
        page = reader[page_num]
        text = page.get_text()
        if search_text in text:
            return page_num
    return -1

def parse_pdf(input_file, output_file):
    sections_to_find = ["Specifications", "Technical requirements"]
    reader = fitz.open(input_file)

    contents_page_num = find_page_with_text(reader, "Contents")
    
    if contents_page_num == -1:
        print(f"'Contents' section not found in {input_file}")
        reader.close()
        return
    
    contents_page = reader[contents_page_num]
    contents_text = contents_page.get_text()
    found_section = None
    for section in sections_to_find:
        if section in contents_text:
            found_section = section
            break
    
    if found_section:
        section_start_index = contents_text.find(found_section)
        spec_page_num_start = int([word for word in contents_text[section_start_index:].split() if word.isdigit()][0]) - 1
        next_section_number = int([word for word in contents_text[section_start_index:].split() if word.isdigit()][1]) - 1
        extracted_text = ""
        for page_num in range(spec_page_num_start, next_section_number + 1):
            page_text = reader[page_num].get_text()
            extracted_text += page_text + "\n"

        with open(output_file, "w", encoding="utf-8") as txt_file:
            txt_file.write(f"{found_section} for {os.path.basename(input_file)}:\n")
            txt_file.write(extracted_text)

    reader.close()

def main():
    parser = argparse.ArgumentParser(description="Parse PDF and extract specific sections.")
    parser.add_argument("input_file", help="Path to the input PDF file")
    parser.add_argument("output_file", help="Path to the output text file")
    args = parser.parse_args()

    parse_pdf(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
