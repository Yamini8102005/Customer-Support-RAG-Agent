import os
import sys

def verify():
    print("Checking dependencies...")
    modules = [
        "streamlit",
        "langchain",
        "langchain_community",
        "langchain_google_genai",
        "faiss",
        "pypdf",
        "reportlab",
        "dotenv"
    ]
    
    missing = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"  [OK] {mod} is installed.")
        except ImportError:
            print(f"  [FAIL] {mod} is NOT installed.")
            missing.append(mod)
            
    if missing:
        print("\nError: Some dependencies are missing. Please run 'pip install -r requirements.txt'")
        sys.exit(1)
        
    print("\nChecking file paths...")
    pdf_path = os.path.join("data", "gigacorp_faq.pdf")
    if os.path.exists(pdf_path):
        print(f"  [OK] FAQ PDF exists at: {pdf_path}")
    else:
        print(f"  [FAIL] FAQ PDF missing at: {pdf_path}")
        
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"  [OK] .env file exists.")
        with open(env_path, "r") as f:
            content = f.read()
            if "GEMINI_API_KEY=" in content and len(content.split("GEMINI_API_KEY=")[1].strip()) > 5:
                print("  [OK] GEMINI_API_KEY appears to be configured in .env.")
            else:
                print("  [!] GEMINI_API_KEY is empty in .env. Please fill it in to run the app.")
    else:
        print(f"  [FAIL] .env file is missing. Please copy .env.example to .env.")

    print("\nVerification process complete!")

if __name__ == "__main__":
    verify()
