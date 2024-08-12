from flask import Flask, request, render_template
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

app = Flask(__name__)
# can nico modify this
def create_xml_template(text):
    root = ET.Element("TEI", {
        "xml:id": "TEI_ujl_fxt_s1c",
        "xml:lang": "en",
        "xmlns": "http://www.tei-c.org/ns/1.0"
    })
    teiHeader = ET.SubElement(root, "teiHeader", {"xml:lang": "en"})
    fileDesc = ET.SubElement(teiHeader, "fileDesc")
    
    # titleStmt remains unchanged
    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    ET.SubElement(titleStmt, "title", {"type": "main"})

    # publicationStmt setup, with dynamic idno based on tag F
    publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
    ET.SubElement(publicationStmt, "authority").text = "LALP"
    idno_pub = ET.SubElement(publicationStmt, "idno")
    idno_pub.text = extract_tag('F', text)

 
    # notesStmt
    notesStmt = ET.SubElement(fileDesc, "notesStmt")
    ET.SubElement(notesStmt, "note")  # You can remove this line if it's a placeholder
    
    # Add <note> tags for <MF> and <MI> if content is not "X"
    insert_note_if_not_x(notesStmt, "MF", text)
    insert_note_if_not_x(notesStmt, "MI", text)

    # sourceDesc and msIdentifier setup, with dynamic repository and idno based on tags Q and U
    sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
    msDesc = ET.SubElement(sourceDesc, "msDesc")
    msIdentifier = ET.SubElement(msDesc, "msIdentifier")
    repository = ET.SubElement(msIdentifier, "repository", {"ref": extract_tag('Q', text)})
    idno_ms = ET.SubElement(msIdentifier, "idno")
    idno_ms.text = extract_tag('U', text)
    
    # profileDesc
    profileDesc = ET.SubElement(teiHeader, "profileDesc")
    correspDesc = ET.SubElement(profileDesc, "correspDesc")
    correspAction_sent = ET.SubElement(correspDesc, "correspAction", {"type": "sent"})
    
    # Process the <ST> tag to set the appropriate role in <persName>
    process_tag_ST(text, correspAction_sent)

    ET.SubElement(correspAction_sent, "settlement", {"ref": ""})
    
    # Extract and format the date for <D> tag
    date_value = extract_tag('D', text)
    formatted_date = format_date(date_value)  # Format the date
    ET.SubElement(correspAction_sent, "date", {"when": formatted_date, "cert": "", "evidence": ""})

    correspAction_received = ET.SubElement(correspDesc, "correspAction", {"type": "received"})

    # Process the <RT> tag to set the appropriate role in <persName> for received action
    process_tag_RT(text, correspAction_received)

    ET.SubElement(correspAction_received, "settlement", {"ref": ""})

    creation = ET.SubElement(profileDesc, "creation")
    ET.SubElement(creation, "persName", {"role": "author", "ref": "psn:hand_1"})

    
    # Implement additional processing based on tag values
    textClass = ET.SubElement(profileDesc, "textClass")
    process_tag_T(text, textClass)
    process_tag_G1(text, textClass)
    process_tag_G2(text, textClass)
    process_tag_CF(text, textClass)
    process_tag_CO(text, textClass)

    # handNotes
    handNotes = ET.SubElement(profileDesc, "handNotes")
    ET.SubElement(handNotes, "handNote", {"xml:id": "", "scope": ""})

    # revisionDesc
    revisionDesc = ET.SubElement(teiHeader, "revisionDesc")
    ET.SubElement(revisionDesc, "change")

    # Facsimile section
    facsimile = ET.SubElement(root, "facsimile", {"xml:base": ""})
    ET.SubElement(facsimile, "graphic", {"xml:id": "", "url": "", "mimeType": ""})

    # Text section
    text_element = ET.SubElement(root, "text", {"xml:lang": "en"})
    body = ET.SubElement(text_element, "body")
    ET.SubElement(body, "div", {"type": "address"})
    div_letter = ET.SubElement(body, "div", {"type": "letter", "facs": ""})
    
    # Create the <p> element
    p = ET.SubElement(div_letter, "p")

    # Extract letter text after the <ML> tag and add it with line breaks within the <p> element
    letter_text = extract_letter_text(text)
    if letter_text:
        add_letter_text_with_line_breaks(p, letter_text)

    closer = ET.SubElement(div_letter, "closer")
    ET.SubElement(closer, "signed")
    postscript = ET.SubElement(div_letter, "postscript")
    p_ps = ET.SubElement(postscript, "p")
    ET.SubElement(p_ps, "lb")
    ET.SubElement(postscript, "signed")

    # Pretty print the final XML
    rough_string = ET.tostring(root, encoding='unicode', method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="UTF-8")

def add_letter_text_with_line_breaks(p, letter_text):
    # Split the text into lines
    lines = letter_text.splitlines()

    # Iterate through the lines
    for i, line in enumerate(lines):
        if i > 0:
            # Add an <lb break="yes"/> tag before each new line (except the first one)
            lb = ET.SubElement(p, "lb", {"break": "yes"})
            lb.tail = line
        else:
            # For the first line, directly set it as text
            p.text = line
            
def extract_tag(tag, text):
    patterns = {
        'F': "<F\s+(.*?)>",
        'Q': "<Q\s+(.*?)>",
        'U': "<U\s+(.*?)>",
        'T': "<T\s+(.*?)>",
        'G1': "<G\s+(.*?)/",
        'G2':"/\s+(.*?)>",
        'ST': "<ST\s+(.*?)>",
        'SN': "<SN\s+(.*?)>",
        'SA': "<SA\s+(.*?)>",
        'SG': "<SG\s+(.*?)>",
        'SJ': "<SJ\s+(.*?)>",
        'SP': "<SP\s+(.*?)>",
        'AN': "<AN\s+(.*?)>",
        'AA': "<AA\s+(.*?)>",
        'AG': "<AG\s+(.*?)>",
        'AJ': "<AJ\s+(.*?)>",
        'AP': "<AP\s+(.*?)>",
        'O': "<O\s+(.*?)>",
        'RT': "<RT\s+(.*?)>",
        'RN': "<RN\s+(.*?)>",
        'RA': "<RA\s+(.*?)>",
        'RG': "<RG\s+(.*?)>",
        'RJ': "<RJ\s+(.*?)>",
        'L': "<L\s+(.*?)>",
        'D': "<D\s+(.*?)>",
        'X': "<X\s+(.*?)>",
        'WC': "<WC\s+(.*?)>",
        'WD': "<WD\s+(.*?)>",
        'WA': "<WA\s+(.*?)>",
        'WT': "<WT\s+(.*?)>",
        'CF': "<CF\s+(.*?)>",
        'CO': "<CO\s+(.*?)>",
        'MF': "<MF\s+(.*?)>",
        'MI': "<MI\s+(.*?)>",
        'ML': "<ML\s+(.*?)>"
    }
    pattern = patterns.get(tag, "")
    match = re.search(pattern, text)
    return match.group(1) if match else ""

def process_tag_ST(text, parent_element):
    content = extract_tag('ST', text).lower()
    
    # Determine the role based on the content of the ST tag
    role = ""
    if "applicant" in content:
        role = "applicant"
    elif "other" in content:
        role = "other"
    elif "official" in content:
        role = "official"
    
    # Add the <persName> element with the appropriate role
    if role:
        ET.SubElement(parent_element, "persName", {"ref": "", "role": role})

def process_tag_RT(text, parent_element):
    content = extract_tag('RT', text).lower()
    
    # Determine the role based on the content of the ST tag
    role = ""
    if "applicant" in content:
        role = "applicant"
    elif "other" in content:
        role = "other"
    elif "official" in content:
        role = "official"
    
    # Add the <persName> element with the appropriate role
    if role:
        ET.SubElement(parent_element, "persName", {"ref": "", "role": role})
        
def format_date(date_str):
    # Convert "yyyy mm dd" to "yyyy-mm-dd"
    return date_str.replace(" ", "-")

def insert_note_if_not_x(notesStmt, tag, text):
    content = extract_tag(tag, text)
    if content and content != "X":
        note = ET.SubElement(notesStmt, "note")
        note.text = content

def extract_letter_text(text):
    # Find the position of the <ML> tag
    ml_tag = "<ML"
    start_pos = text.find(ml_tag)

    if start_pos != -1:
        # Find the end of the <ML> tag
        end_ml_tag = text.find(">", start_pos) + 1
        
        # Extract the text after the <ML> tag
        letter_text = text[end_ml_tag:].strip()
        return letter_text
    else:
        return ""


def process_tag_T(text, parent_element):
    content = extract_tag('T', text)
    mappings = {
        "1a": "gen:OFFICIAL",
        "1b": "gen:UNOFFICIAL"
    }
    for key, value in mappings.items():
        if key in content:
            ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": value})

def process_tag_G1(text, parent_element):
    content = extract_tag('G1', text)
    mappings = {
        "A 1": "gen:AUTHENTICITY_A1",
        "A 2": "gen:AUTHENTICITY_A2",
        "N 1": "gen:AUTHENTICITY_N1",
        "N 2": "gen:AUTHENTICITY_N2",
        "N 5": "gen:AUTHENTICITY_N5",
        "NC": "gen:AUTHENTICITY_NC",
        "?": "gen:AUTHENTICITY_NC",
    }

    for key, value in mappings.items():
        if key in content:
            ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": value}) 
            
def process_tag_G2(text, parent_element):
    content = extract_tag('G2', text)
    mappings = {
        "L?": "gen:WRITING_SKILL_L_UNCERTAIN",
        "L": "gen:WRITING_SKILL_L",
        "LH": "gen:WRITING_SKILL_LH",
        "H?": "gen:WRITING_SKILL_H_UNCERTAIN",
        "H": "gen:WRITING_SKILL_H"
    }
    
    # Find all matches for the G2 tag
    matched_keys = set()
    
    # First match the longer patterns "L?" and "H?"
    if "LH" in content:
        matched_keys.add("LH")
    elif "L?" in content:
        matched_keys.add("L?")
    elif "L" in content:
        matched_keys.add("L")
    
    if "H?" in content:
        matched_keys.add("H?")
    elif "H" in content and "LH" not in content:
        matched_keys.add("H")

    # Add the matched keys to the parent element
    for key in matched_keys:
        ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": mappings[key]})


def process_tag_CF(text, parent_element):
    content = extract_tag('CF', text).lower()
    mappings = {
        "application": "gen:CF_APPLICATION",
        "re-application": "gen:CF_RE-APPLICATION",
        "reminder": "gen:CF_REMINDER",
        "renewal": "gen:CF_RENEWAL",
        "change": "gen:CF_CHANGE",
        "assistance": "gen:CF_ASSISTANCE",
        "notification": "gen:CF_NOTIFICATION",
        "report": "gen:CF_REPORT",
        "certificate": "gen:CF_CERTIFICATE",
        "query": "gen:CF_QUERY",
        "thanks": "gen:CF_THANKS",
        "apology": "gen:CF_APOLOGY",
        "defence": "gen:CF_DEFENCE",
        "testimonial": "gen:CF_TESTIMONIAL",
        "other": "gen:CF_OTHER"
    }
    for key, value in mappings.items():
        if key in content:
            ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": value})
            
def process_tag_CO(text, parent_element):
    content = extract_tag('CO', text).lower()
    mappings = {
       "application pending": "gen:CO_APPLICATION_PENDING",
       "relief: money": "gen:CO_RELIEF_MONEY",
       "relief: rent": "gen:CO_RELIEF_RENT",
       "relief: clothes": "gen:CO_RELIEF_CLOTHES",
       "relief: food": "gen:CO_RELIEF_FOOD",
       "relief: coal": "gen:CO_RELIEF_COAL",
       "relief: assistance": "gen:CO_RELIEF_ASSISTANCE",
       "relief": "gen:CO_RELIEF",
       "payment halt": "gen:CO_PAYMENT_HALT",
       "payment increase": "gen:CO_PAYMENT_INCREASE",
       "payment modality": "gen:CO_PAYMENT_MODALITY",
       "payment pending/delayed": "gen:CO_PAYMENT_PENDING",
       "employment": "gen:CO_EMPLOYMENT",
       "certificate": "gen:CO_CERTIFICATE",
       "return to parish": "gen:CO_RETURN_PARISH",
       "attendance in person": "gen:CO_ATTENDANCE",
       "removal to parish": "gen:CO_REMOVAL",
       "pass": "gen:CO_PASS",
       "account": "gen:CO_ACCOUNT",
       "applicant: situation": "gen:CO_APPLICANT_SITUATION",
       "applicant: health": "gen:CO_APPLICANT_HEALTH",
       "legal action": "gen:CO_LEGAL_ACTION",
       "release from prison": "gen:CO_PRISON_RELEASE",
       "settlement": "gen:CO_SETTLEMENT",
       "correspondence": "gen:CO_CORRESPONDENCE",
       "debt": "gen:CO_DEBT",
       "child support": "gen:CO_CHILD_SUPPORT",
       "other": "gen:CO_OTHER"
    }

    # Split content by commas and strip whitespace
    components = [component.strip() for component in content.split(",")]

    # Track which general keys have specific matches
    specific_matched_keys = set()

    # First pass: Add specific matches and track the general keys they belong to
    for component in components:
        for key, value in mappings.items():
            if key in component:
                if ":" in key:
                    # This is a specific key, so add it and mark the general key
                    ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": value})
                    general_key = key.split(":")[0].strip()
                    specific_matched_keys.add(general_key)
                break  # Stop after first match within this component

    # Second pass: Add general matches if they weren't covered by specific ones
    for component in components:
        general_key = component.split(":")[0].strip()
        if general_key in mappings and general_key not in specific_matched_keys:
            ET.SubElement(parent_element, "catRef", {"scheme": "gen:LALP_letter_types", "target": mappings[general_key]})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_xml', methods=['POST'])
def generate_xml():
    text_input = request.form['text_input']
    xml_output = create_xml_template(text_input)
    return render_template('index.html', xml_output=xml_output.decode('UTF-8'))

if __name__ == '__main__':
    app.run(debug=True)