# Student Management System

Complete CRUD web application for the college SOP.

## Stack
HTML, CSS, Python Flask, SQLite, REST API, Postman, Git/GitHub.

## Features
Create, Read, Update, Delete, Search, validation, duplicate handling and REST APIs.

## Run
```bash
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`

## API
GET `/api/students/`
GET `/api/students/<id>/`
POST `/api/students/`
PUT/PATCH `/api/students/<id>/`
DELETE `/api/students/<id>/`

## GitHub
```bash
git init
git add .
git commit -m "Initial CRUD student management application"
git branch -M main
git remote add origin YOUR_GITHUB_URL
git push -u origin main
```
