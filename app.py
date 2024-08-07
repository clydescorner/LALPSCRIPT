from flask import Flask, request, render_template
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

app = Flask(__name__)

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
    ET.SubElement(notesStmt, "note")

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
    ET.SubElement(correspAction_sent, "persName", {"ref": "", "role": "applicant"})
    ET.SubElement(correspAction_sent, "settlement", {"ref": ""})
    ET.SubElement(correspAction_sent, "date", {"when": extract_tag('D', text), "cert": "", "evidence": ""})
    correspAction_received = ET.SubElement(correspDesc, "correspAction", {"type": "received"})
    ET.SubElement(correspAction_received, "persName", {"ref": "", "role": ""})
    ET.SubElement(correspAction_received, "settlement", {"ref": ""})

    creation = ET.SubElement(profileDesc, "creation")
    ET.SubElement(creation, "persName", {"role": "author", "ref": "psn:hand_1"})
    
    # Implement additional processing based on tag values
    textClass = ET.SubElement(profileDesc, "textClass")
    process_tag_T(text, textClass)
    process_tag_G1(text, textClass)
    process_tag_G2(text, textClass)
    process_tag_CF(text, textClass)

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
    ET.SubElement(div_letter, "pb", {"facs": "", "break": "yes"})
    opener = ET.SubElement(div_letter, "opener")
    ET.SubElement(opener, "dateline")
    ET.SubElement(opener, "salute")
    p = ET.SubElement(div_letter, "p")
    ET.SubElement(p, "lb", {"break": "yes"})
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
