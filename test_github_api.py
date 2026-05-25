from analyzer.github_api import GitHubClient, GitHubAPIError
from decouple import config

def test_github_client():
    """Test complet du client GitHub API"""
    
    # 1. Récupérer le token depuis .env
    token = str(config('GITHUB_TEST_TOKEN'))
    print(f"✅ Token chargé : {token[:10]}...")
    
    # 2. Créer le client
    try:
        client = GitHubClient(token)
        print("✅ Client GitHub créé")
    except Exception as e:
        print(f"❌ Erreur création client : {e}")
        return
    
    # 3. Tester les infos utilisateur
    try:
        user_info = client.get_user_info()
        print(f"\n👤 Utilisateur : {user_info['login']}")
        print(f"   Nom : {user_info.get('name', 'N/A')}")
        print(f"   Repos publics : {user_info['public_repos']}")
    except GitHubAPIError as e:
        print(f"❌ Erreur user info : {e}")
        return
    
    # 4. Tester la liste des repos
    repos = []
    files = []
    first_repo = None
    
    try:
        repos = client.get_user_repos(per_page=5)
        print(f"\n📚 Repositories (5 premiers) :")
        for repo in repos[:5]:
            print(f"   - {repo['full_name']} ({repo['language']})")
    except GitHubAPIError as e:
        print(f"❌ Erreur repos : {e}")
        return
    
    # 5. Tester l'arbre de fichiers (sur le premier repo)
    if repos:
        first_repo = repos[0]
        try:
            print(f"\n📁 Fichiers de {first_repo['full_name']} :")
            files = client.get_repo_tree(
                owner=first_repo['owner'],
                repo=first_repo['name'],
                branch=first_repo['default_branch']
            )
            print(f"   Total : {len(files)} fichiers")
            
            # Afficher les 10 premiers
            for file in files[:10]:
                size_kb = file['size'] / 1024
                print(f"   - {file['path']} ({size_kb:.1f} KB)")
                
        except GitHubAPIError as e:
            print(f"❌ Erreur tree : {e}")
            return
    
    # 6. Tester le contenu d'un fichier
    if files and first_repo:
        # Chercher un fichier README
        readme = next((f for f in files if 'README' in f['path'].upper()), files[0])
        
        try:
            print(f"\n📄 Contenu de {readme['path']} :")
            content = client.get_file_content(
                owner=first_repo['owner'],
                repo=first_repo['name'],
                file_path=readme['path']
            )
            
            # Afficher les 10 premières lignes
            lines = content['content'].split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            
            if len(content['content'].split('\n')) > 10:
                print("   ...")
                
        except GitHubAPIError as e:
            print(f"❌ Erreur content : {e}")
    
    print("\n✅ Tous les tests sont passés !")

if __name__ == '__main__':
    test_github_client()


# Made with Bob