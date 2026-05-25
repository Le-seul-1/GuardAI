# RepoGuard AI

## 🧠 Project Overview

RepoGuard AI is a lightweight AI-powered web application that helps developers understand, analyze, and secure their code quickly.

Many developers today use AI tools to generate code, but they often:
- do not fully understand what the code does
- introduce security vulnerabilities without noticing
- lack time to manually review everything

RepoGuard AI solves this by providing instant AI-based code review and security analysis.

---

## 🎯 Problem Statement

Developers using AI-generated code often face:
- hidden security vulnerabilities
- poor code structure
- lack of understanding of their own code
- time-consuming manual debugging

There is a need for a fast, simple tool that:
- explains code clearly
- detects security issues
- suggests improvements

---

## 🚀 Solution

RepoGuard AI allows users to:

1. Input code manually OR select a file from a GitHub repository (simplified via token)
2. Automatically analyze the code using AI
3. Receive:
   - explanation of what the code does
   - detected security vulnerabilities
   - improved version of the code

---

## ⚙️ Core Features (MVP)

### 1. GitHub Integration (Simplified)
- User provides a GitHub Personal Access Token
- App fetches list of repositories
- User selects a repository
- App displays list of files (limited view)

---

### 2. Smart File Selection
- AI selects the most relevant 2–3 files for security review
- Focus on files likely to contain vulnerabilities (backend, logic, config files)

---

### 3. Code Analysis (Core Feature)
For each selected file:
- Explain what the code does
- Identify bugs or vulnerabilities
- Suggest improvements
- Provide a fixed version of the code

---

### 4. AI Security Report
Generate a final report containing:
- summary of repository
- list of analyzed files
- detected issues
- recommended fixes

---

## 🧠 AI Role (IBM Bob)

IBM Bob is used to:
- analyze source code
- understand code structure
- detect potential security vulnerabilities
- generate improved versions of code
- select important files from repository structure

---

## 🖥️ Technical Stack

### Backend
- Django (Python)
- Django Templates (no frontend framework)

### Frontend
- Django HTML templates
- Basic JavaScript (fetch requests if needed)

### Database
- SQLite (default Django DB)

### External APIs
- GitHub API (for repository and file listing)
- IBM Bob (AI processing)

---

## 🔐 GitHub Integration (Simplified Approach)

To avoid complex OAuth:
- User manually provides a GitHub Personal Access Token
- Token is used to fetch:
  - repositories
  - repository files

No OAuth login system is implemented.

---

## 📂 Workflow

1. User enters GitHub token
2. System fetches repositories
3. User selects a repository
4. System fetches file list
5. AI selects 2–3 critical files
6. User confirms or continues
7. AI analyzes selected files
8. System displays:
   - explanation
   - vulnerabilities
   - improved code
   - final report

---

## ⚠️ Constraints

- No full repository analysis (only selected files)
- No GitHub OAuth implementation
- No automatic push to GitHub
- Focus on simplicity and working MVP
- Limited time implementation (hackathon prototype)

---

## 🎯 Goals

The goal is to demonstrate:
- practical AI-assisted code understanding
- security improvement using AI
- developer productivity enhancement
- simple but effective GitHub integration

---

## 🏆 Expected Output

A working prototype where:
- user selects a GitHub repo
- AI selects important files
- AI analyzes code
- user receives clear and useful feedback

---

## 💡 Future Improvements (Not in MVP)

- automatic GitHub pull request fixes
- full repository scanning
- authentication system (OAuth, Clerk)
- multi-language code support
- real-time IDE integration