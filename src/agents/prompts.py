"""Prompts for VLM-based document analysis."""

# System prompt for the agent
SYSTEM_PROMPT = """You are an expert document analysis assistant specializing in Indian government and administrative documents. You can analyze documents in both Hindi and English.

Your capabilities:
1. Extract structured data from tables (voter lists, registries, etc.)
2. Analyze forms and extract field values
3. Detect and read stamps/seals on official documents
4. Interpret charts and graphs
5. Handle handwritten annotations

Guidelines:
- Always return valid JSON output
- Preserve the original language of the document (Hindi or English)
- Be careful with numeric values - verify them multiple times
- For tables, maintain row-column structure in your output
- If you're unsure about any value, include a confidence score
- Flag any potentially incorrect or ambiguous extractions

Document Context:
{document_context}

Language: {language}"""

# Table analysis prompt (English)
TABLE_ANALYSIS_PROMPT = """Analyze this table and extract its structured data.

Instructions:
1. Identify the table headers
2. Extract each row with its corresponding values
3. Handle merged cells appropriately
4. Preserve numeric formatting (commas, decimals)

Return your analysis as JSON with this structure:
{{
    "headers": ["column1", "column2", ...],
    "rows": [
        {{"column1": "value1", "column2": "value2", ...}},
        ...
    ],
    "notes": "Any observations about table structure or data quality"
}}

If the table has Hindi text, keep the Hindi text in Devanagari script.
For numeric columns, try to extract clean numeric values.

Table region from document:"""

# Table analysis prompt (Hindi)
TABLE_HINDI_PROMPT = """इस तालिका का विश्लेषण करें और इसका संरचित डेटा निकालें।

निर्देश:
1. तालिका के शीर्षक (headers) पहचानें
2. प्रत्येक पंक्ति को उसके संबंधित मानों के साथ निकालें
3. मिली हुई कोशिकाओं (merged cells) को उचित रूप से संभालें
4. संख्यात्मक प्रारूपण (अल्पविराम, दशमलव) को संरक्षित रखें

अपना विश्लेषण JSON के रूप में लौटाएं:
{{
    "headers": ["स्तंभ1", "स्तंभ2", ...],
    "rows": [
        {{"स्तंभ1": "मान1", "स्तंभ2": "मान2", ...}},
        ...
    ],
    "notes": "तालिका संरचना या डेटा गुणवत्ता के बारे में टिप्पणी"
}}

तालिका से हिंदी पाठ को देवनागरी लिपि में रखें।
संख्यात्मक स्तंभों के लिए, स्वच्छ संख्यात्मक मान निकालने का प्रयास करें।

दस्तावेज़ से तालिका क्षेत्र:"""

# Form analysis prompt
FORM_ANALYSIS_PROMPT = """Analyze this form and extract all field values.

Instructions:
1. Identify each field label and its corresponding value
2. Handle checkboxes (checked/unchecked)
3. Extract handwritten values if present
4. Note any stamps or official seals

Return your analysis as JSON:
{{
    "fields": {{
        "field_label_1": "value1",
        "field_label_2": "value2",
        ...
    }},
    "checkboxes": {{
        "checkbox_label": true/false,
        ...
    }},
    "stamps": ["description of any stamps/seals"],
    "handwritten_values": {{
        "field": "handwritten value"
    }},
    "notes": "Any observations about form quality or ambiguous values"
}}

For Hindi forms, keep field labels and values in their original language.
Form region from document:"""

# Stamp/Seal analysis prompt
STAMP_ANALYSIS_PROMPT = """Analyze this stamp or seal on the document.

Instructions:
1. Read any text on the stamp (may be circular or curved)
2. Identify the type of stamp (official seal, date stamp, signature stamp, etc.)
3. Extract any dates, names, or official titles
4. Note the color and approximate size

Return your analysis as JSON:
{{
    "text_content": "All readable text on the stamp",
    "stamp_type": "official_seal|date_stamp|signature_stamp|other",
    "organization": "Name of organization if visible",
    "date": "Any date visible on the stamp",
    "color": "Primary color of the stamp",
    "confidence": 0.0-1.0 confidence score,
    "notes": "Any additional observations"
}}

Stamp region from document:"""

# Chart analysis prompt
CHART_ANALYSIS_PROMPT = """Analyze this chart or graph and extract its data.

Instructions:
1. Identify the chart type (bar, line, pie, scatter, etc.)
2. Read axis labels and titles
3. Extract data points or values
4. Note any legends or keys

Return your analysis as JSON:
{{
    "chart_type": "bar|line|pie|scatter|other",
    "title": "Chart title if present",
    "x_axis": {{
        "label": "X axis label",
        "values": [...]
    }},
    "y_axis": {{
        "label": "Y axis label",
        "values": [...]
    }},
    "data_points": [
        {{"x": value, "y": value, "label": "optional"}},
        ...
    ],
    "legend": {{
        "series_name": "color/description"
    }},
    "summary": "Brief summary of what the chart shows",
    "notes": "Any observations about chart quality or readability"
}}

Chart region from document:"""
