import fitz
import json
import os
from llama_cpp import Llama
from pathlib import Path

def debug_model_path():
    """Debug function to check model path and directory contents."""
    model_path = os.getenv("MODEL_PATH")
    print(f"\nDebug Information:")
    print(f"1. MODEL_PATH environment variable: {model_path}")
    
    # Check if the direct path exists
    print(f"2. Does direct model path exist? {os.path.exists(model_path)}")
    
    # Check the base directory
    base_dir = Path("/app/model")
    print(f"3. Base directory contents (/app/model):")
    try:
        for item in base_dir.iterdir():
            print(f"   - {item}")
            if item.is_dir():
                print(f"     Contents of {item}:")
                for subitem in item.iterdir():
                    print(f"     * {subitem}")
    except Exception as e:
        print(f"   Error reading directory: {e}")
    
    return model_path

def initialize_model():
    """Initialize the LLM model with proper error handling."""
    model_path = debug_model_path()  # This will print debug info
    
    if not model_path:
        raise ValueError("MODEL_PATH environment variable is not set")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    try:
        print(f"\nAttempting to load model from: {model_path}")
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0
        )
        return model
    except Exception as e:
        print(f"Error initializing model: {e}")
        raise

# ... rest of your code remains the same ...

def chunk_text(text, max_tokens=512):
    """Split the text into chunks of max_tokens."""
    tokens = text.split()
    chunks = []
    
    while tokens:
        chunk = tokens[:max_tokens]
        chunks.append(" ".join(chunk))
        tokens = tokens[max_tokens:]
    
    return chunks

def extract_text(pdf_path):
    """Extract text from a PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        raise
    finally:
        if 'doc' in locals():
            doc.close()

def categorize_text(text, model):
    """Generate a structured response using the LLM."""
    chunks = chunk_text(text)
    all_responses = []
    
    for chunk in chunks:
        try:
            prompt = f"""
            Extract and categorize data into structured JSON format with fields like 'name', 'grade', 'course', 
            credits, year, etc. Ensure that multiple categories are separated into rows, and if applicable, 
            provide multiple instances. 
            
            Text to process: {chunk}
            
            Format the response as valid JSON.
            """
            
            response = model.create_completion(
                prompt,
                max_tokens=512,
                temperature=0.7,
                stop=["</s>"],
                echo=False
            )
            
            if response and 'choices' in response and response['choices']:
                output_text = response['choices'][0].get('text', '').strip()
                try:
                    # Attempt to parse as JSON
                    structured_output = json.loads(output_text)
                    all_responses.append(structured_output)
                except json.JSONDecodeError:
                    # Fall back to plain text if not valid JSON
                    all_responses.append({"text": output_text})
            else:
                print(f"Warning: Unexpected response format: {response}")
                all_responses.append({"error": "No valid output text found"})
                
        except Exception as e:
            print(f"Error processing chunk: {e}")
            all_responses.append({"error": str(e)})
    
    return all_responses

def process_pdf(pdf_path):
    """Process a PDF file and return categorized data."""
    try:
        # Extract text from PDF
        pdf_text = extract_text(pdf_path)
        
        # Initialize model
        model = initialize_model()
        
        # Process the text
        categorized_data = categorize_text(pdf_text, model)
        
        # Save results
        output_path = pdf_path.replace('.pdf', '_results.json')
        with open(output_path, 'w') as f:
            json.dump(categorized_data, f, indent=2)
            
        return categorized_data
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise

if __name__ == "__main__":
    try:
        pdf_path = "data/transcript.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        results = process_pdf(pdf_path)
        print("Processing completed successfully")
        print("Results:", json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"Application error: {e}")
        exit(1)