# 🌿 FloraCure — Plant Disease Expert System

> An AI-powered plant diagnosis web application built with Django.  
> Upload a plant photo, select symptoms, and get an instant diagnosis with cure recommendations.


## ✨ Features

- 🔬 **Smart Diagnosis** — Rule-based expert system covering 30+ plant diseases
- 📊 **Dashboard** — Track total diagnoses, active treatments & cured plants
- 🌤️ **Weather Integration** — Live weather with plant-specific care tips
- 📄 **PDF Reports** — Download professional diagnosis reports
- 👤 **User Accounts** — Register, login, profile management
- 📱 **Fully Responsive** — Mobile, tablet & desktop friendly
- 🔐 **Secure** — Login required for all pages except welcome & register


## 🛠️ Tech Stack

| Technology | Usage |
|------------|-------|
| Python 3.13 | Backend language |
| Django 6.0 | Web framework |
| SQLite | Database |
| Tailwind CSS | Frontend styling |
| ReportLab | PDF generation |
| OpenWeatherMap API | Weather data |

---

## 📁 Project Structure

```
FloraCure/
├── FloraCure/          # Project config (settings, urls)
├── floraApp/           # Main app — views, models, forms, admin
├── templates/          # All HTML templates
│   ├── base.html       # Base template with navbar
│   ├── home.html
│   ├── dashboard.html
│   ├── diagnose.html
│   ├── hh.html         # History
│   └── profile.html
├── Static/             # CSS, images
├── .gitignore
├── requirements.txt
└── manage.py
```

---

## 🌿 Plant Diseases Covered

| Category | Diseases |
|----------|----------|
| 🍃 Leaf | Fungal Leaf Spot, Powdery Mildew, Rust Fungus, Chlorosis & more |
| 🌿 Stem | Root/Stem Rot, Damping Off, Crown Gall & more |
| 🌱 Root | Root Rot, Nutrient Deficiency & more |
| 🌸 Flower/Fruit | Blossom End Rot, Pollination Issues & more |
| 🐛 Pest | Spider Mites, Mealybugs, Whiteflies, Thrips & more |
| 🌡️ Environmental | Sunscald, Frost Injury, Fusarium Wilt & more |

---

## 👨‍💻 Author

**Munavvar Khan**  
Final Year Project — 2026

[![GitHub](https://img.shields.io/badge/GitHub-khanmunavvar-black?logo=github)](https://github.com/khanmunavvar)

---

## 📄 License

This project is for educational purposes.
