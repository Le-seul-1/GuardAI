import json
from groq import Groq
from decouple import config

class GroqAIError(Exception):
    """Exception pour les erreurs Groq AI"""
    pass

def analyze_code(code: str) -> dict:
    """
    Analyse le code avec l'API Groq en utilisant le modèle llama-3.3-70b-versatile.
    """
    try:
        client = Groq(
            api_key=config("GROQ_API_KEY")
        )

        prompt = f'''
Analyze this code and return a JSON object with the exact following structure:
{{
    "explanation": "Brief explanation of what the code does",
    "vulnerabilities": [
        {{
            "type": "Name of the vulnerability (e.g., SQL Injection)",
            "severity": "low", "medium", "high", or "critical",
            "description": "Why it is vulnerable",
            "recommendation": "How to fix it"
        }}
    ],
    "improvements": "General code quality improvements",
    "improved_code": "The full code with fixes applied"
}}

Code:
{code}
'''

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior security engineer. You must return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        response_content = chat_completion.choices[0].message.content
        
        try:
            result = json.loads(response_content)
            # Ensure missing fields have defaults
            return {
                'explanation': result.get('explanation', ''),
                'vulnerabilities': result.get('vulnerabilities', []),
                'improved_code': result.get('improved_code', ''),
                'improvements': result.get('improvements', '')
            }
        except json.JSONDecodeError:
            raise GroqAIError("Impossible de parser la réponse JSON de l'IA")
            
    except Exception as e:
        raise GroqAIError(f"Erreur API Groq : {str(e)}")
