# -*- coding: utf-8 -*-
from analyzer.ibm_bob_ai import IBMBobClient, create_ibm_bob_client

def test_ibm_bob():
    """Test du client IBM Bob AI"""
    
    # 1. Créer le client
    client = create_ibm_bob_client()
    print("[OK] Client IBM Bob AI cree")
    
    # 2. Tester la sélection de fichiers
    mock_files = [
        {'path': 'src/auth/login.py', 'size': 5000},
        {'path': 'src/models/user.py', 'size': 3000},
        {'path': 'config/settings.py', 'size': 2000},
        {'path': 'tests/test_auth.py', 'size': 4000},
        {'path': 'README.md', 'size': 1000},
    ]
    
    selected = client.select_critical_files(mock_files, max_files=3)
    print(f"\n[FILES] Fichiers selectionnes :")
    for file in selected:
        print(f"   - {file['path']} (score: {file['priority_score']})")
    
    # 3. Tester l'analyse de code
    sample_code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result
"""
    
    print(f"\n[ANALYZE] Analyse du code...")
    analysis = client.analyze_code('login.py', sample_code, 'python')
    
    print(f"\n[RESULTS] Resultats :")
    print(f"   Explication : {analysis['explanation'][:100]}...")
    print(f"   Vulnerabilites : {len(analysis['vulnerabilities'])}")
    print(f"   Score qualite : {analysis['code_quality_score']}/10")
    
    if analysis['vulnerabilities']:
        print(f"\n[WARNING] Vulnerabilites detectees :")
        for vuln in analysis['vulnerabilities']:
            print(f"   - [{vuln['severity'].upper()}] {vuln['type']}")
            print(f"     Ligne {vuln['line']}: {vuln['description']}")
    
    print("\n[OK] Test termine !")

if __name__ == '__main__':
    test_ibm_bob()

# Made with Bob
