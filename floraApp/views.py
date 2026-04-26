from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponse
from .models import Profile, Diagnosis
from .forms import ProfileForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import requests
import io


# ─── Public Views ─────────────────────────────────────────────────────────────

def welcome(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'welcome.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        return render(request, "login.html", {"error": "Invalid username or password."})
    return render(request, "login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email     = request.POST.get("email", "").strip()
        password  = request.POST.get("password", "").strip()

        if not full_name or not email or not password:
            return render(request, "register.html", {"error": "Please fill in all fields."})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "This email is already registered."})

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name  = name_parts[1] if len(name_parts) > 1 else ""

        base_username = full_name.replace(" ", "").lower()
        username = base_username
        counter  = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        Profile.objects.create(user=user)
        login(request, user)
        return redirect("home")

    return render(request, "register.html")


def logout_view(request):
    logout(request)
    return redirect('welcome')


# ─── Protected Views ──────────────────────────────────────────────────────────

@login_required(login_url='/login')
def home(request):
    return render(request, 'home.html')


@login_required(login_url='/login')
def dashboard_view(request):
    user = request.user
    total_diagnoses  = Diagnosis.objects.filter(user=user).count()
    plants_tracked   = Diagnosis.objects.filter(user=user).values("plant_name").distinct().count()
    active_treatments = Diagnosis.objects.filter(user=user, is_cured=False).count()
    cured_this_month = Diagnosis.objects.filter(
        user=user, is_cured=True,
        date__month=now().month, date__year=now().year
    ).count()
    recent_diagnoses = Diagnosis.objects.filter(user=user).order_by("-date")[:5]

    return render(request, "dashboard.html", {
        "total_diagnoses":   total_diagnoses,
        "plants_tracked":    plants_tracked,
        "active_treatments": active_treatments,
        "cured_this_month":  cured_this_month,
        "recent_diagnoses":  recent_diagnoses,
    })


def get_weather(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if not lat or not lon:
        return JsonResponse({"error": "Location not provided"})

    api_key = "7ae268227ffad969179a8c8de6bcd22c"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        data = requests.get(url, timeout=10).json()
        if data.get("cod") == 200:
            temperature = round(data["main"]["temp"])
            condition   = data["weather"][0]["description"].capitalize()
            city_name   = data.get("name", "Your Location")
            cl = condition.lower()
            if "rain"  in cl: tip = "Skip watering today — rain is expected."
            elif "clear" in cl: tip = "Water your plants in the evening to avoid evaporation."
            elif "cloud" in cl: tip = "Good day for watering — overcast skies help retention."
            elif temperature > 35: tip = "Hot day! Water plants early morning or late evening."
            else: tip = "Check your plants and water if soil feels dry."
            return JsonResponse({"temperature": temperature, "condition": condition, "city": city_name, "tip": tip})
        return JsonResponse({"error": data.get("message", "Weather not found")})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def get_diagnosis(symptoms):
    rules = [
        {"keywords": ["Yellowing leaves", "Yellow leaves"],          "disease": "Nutrient Deficiency (Nitrogen)",          "cure": "Add nitrogen-rich fertilizer like urea or compost. Check soil pH (ideal 6-7)."},
        {"keywords": ["Brown leaf tips", "Brown edges"],              "disease": "Leaf Scorch / Salt Burn",                 "cure": "Flush soil with water to remove excess salts. Avoid over-fertilizing."},
        {"keywords": ["Black spots", "Dark spots on leaves"],         "disease": "Fungal Leaf Spot",                        "cure": "Remove infected leaves. Apply copper-based fungicide. Avoid overhead watering."},
        {"keywords": ["White powder", "Powdery coating"],             "disease": "Powdery Mildew",                          "cure": "Spray neem oil or baking soda solution (1 tsp per liter). Improve air circulation."},
        {"keywords": ["Rust spots", "Orange spots"],                  "disease": "Rust Fungus",                             "cure": "Remove affected leaves. Apply sulfur-based fungicide. Keep foliage dry."},
        {"keywords": ["Holes in leaves", "Eaten leaves"],             "disease": "Insect / Caterpillar Damage",             "cure": "Apply neem oil or insecticidal soap. Handpick caterpillars if visible."},
        {"keywords": ["Curling leaves", "Leaf curl"],                 "disease": "Aphid Infestation or Heat Stress",        "cure": "Spray strong water jet to remove aphids. Apply neem oil. Check for overheating."},
        {"keywords": ["Sticky leaves", "Sticky residue"],             "disease": "Aphid / Whitefly Infestation",            "cure": "Apply insecticidal soap or neem oil spray. Introduce ladybugs as natural predators."},
        {"keywords": ["Pale leaves", "Light green leaves"],           "disease": "Chlorosis (Iron/Magnesium Deficiency)",   "cure": "Apply iron chelate or Epsom salt (magnesium sulfate). Check soil pH."},
        {"keywords": ["Drooping leaves", "Limp leaves"],              "disease": "Overwatering or Root Rot",                "cure": "Reduce watering. Check drainage. Remove rotted roots and repot if needed."},
        {"keywords": ["Wilting", "Wilted plant"],                     "disease": "Water Stress / Dehydration",              "cure": "Water deeply and consistently. Mulch around base to retain moisture."},
        {"keywords": ["Stem rot", "Mushy stem"],                      "disease": "Root/Stem Rot (Pythium or Phytophthora)", "cure": "Remove rotted parts. Apply fungicide. Improve soil drainage. Reduce watering."},
        {"keywords": ["Black stem", "Dark stem base"],                "disease": "Damping Off / Blackleg Disease",          "cure": "Remove infected plants. Improve drainage. Apply copper fungicide to soil."},
        {"keywords": ["Leggy stem", "Tall thin stem"],                "disease": "Etiolation (Lack of Light)",              "cure": "Move plant to brighter location. Provide 6-8 hours of sunlight daily."},
        {"keywords": ["Galls on stem", "Lumps on stem"],              "disease": "Crown Gall (Bacterial)",                  "cure": "Remove and destroy infected plants. Avoid wounding plants. Sterilize tools."},
        {"keywords": ["Root rot", "Brown roots", "Smelly roots"],     "disease": "Root Rot (Overwatering / Fungal)",        "cure": "Remove plant from pot. Trim rotted roots. Repot in fresh dry soil. Reduce watering."},
        {"keywords": ["No growth", "Stunted growth"],                 "disease": "Nutrient Deficiency or Compacted Soil",   "cure": "Apply balanced NPK fertilizer. Loosen soil. Check for root-bound condition."},
        {"keywords": ["Flower drop", "Falling flowers", "Bud drop"], "disease": "Environmental Stress / Pollination Issue","cure": "Maintain consistent temperature and humidity. Hand pollinate if needed. Avoid drafts."},
        {"keywords": ["No flowers", "Not blooming"],                  "disease": "Insufficient Light or Nutrients",         "cure": "Increase sunlight. Apply phosphorus-rich fertilizer (bone meal). Prune old growth."},
        {"keywords": ["Fruit rot", "Rotting fruit"],                  "disease": "Blossom End Rot / Fungal Rot",            "cure": "Add calcium to soil. Maintain consistent watering. Apply fungicide if needed."},
        {"keywords": ["Small fruit", "Underdeveloped fruit"],         "disease": "Potassium Deficiency",                    "cure": "Apply potassium-rich fertilizer (potash). Ensure adequate pollination."},
        {"keywords": ["Spider mites", "Fine webbing"],                "disease": "Spider Mite Infestation",                 "cure": "Spray neem oil or miticide. Increase humidity. Isolate infected plant."},
        {"keywords": ["Mealybugs", "White cottony mass"],             "disease": "Mealybug Infestation",                   "cure": "Dab with alcohol-soaked cotton. Apply neem oil. Remove by hand."},
        {"keywords": ["Brown bumps on stem", "Scale insects"],        "disease": "Scale Insect Infestation",                "cure": "Scrape off scales. Apply horticultural oil. Use systemic insecticide if severe."},
        {"keywords": ["Whiteflies", "Tiny white flies"],              "disease": "Whitefly Infestation",                   "cure": "Use yellow sticky traps. Apply neem oil or pyrethrin spray. Remove affected leaves."},
        {"keywords": ["Thrips", "Silver streaks on leaves"],          "disease": "Thrips Infestation",                     "cure": "Apply insecticidal soap or spinosad. Remove heavily infested leaves."},
        {"keywords": ["Sunburn", "Bleached leaves"],                  "disease": "Sunscald / Sunburn",                     "cure": "Move plant to indirect light. Gradually acclimate to full sun. Water adequately."},
        {"keywords": ["Frost damage", "Black after cold"],            "disease": "Frost / Cold Injury",                    "cure": "Remove damaged tissue. Move indoors. Cover with frost cloth in cold weather."},
        {"keywords": ["Wilting despite watering"],                    "disease": "Fusarium Wilt (Fungal)",                 "cure": "Remove infected plant. Solarize soil. Use resistant varieties. Apply fungicide."},
        {"keywords": ["Mosaic pattern", "Distorted leaves"],          "disease": "Viral Mosaic Disease",                   "cure": "No cure available. Remove infected plant immediately. Control aphids (virus vectors)."},
        {"keywords": ["Sooty mold", "Black dusty coating"],           "disease": "Sooty Mold (Secondary Fungal)",          "cure": "Wipe leaves with damp cloth. Control sap-sucking insects causing honeydew."},
    ]
    symptoms_lower = [s.lower() for s in symptoms]
    for rule in rules:
        for keyword in rule["keywords"]:
            if keyword.lower() in symptoms_lower:
                return rule["disease"], rule["cure"]
    return "Unknown Disease", "No symptoms selected or disease not identified. Consult a plant expert."


@login_required(login_url='/login')
def diagnose_view(request):
    symptom_groups = [
        {"icon": "🍃", "label": "Leaf Problems",           "symptoms": ["Yellowing leaves","Brown leaf tips","Black spots","White powder","Rust spots","Holes in leaves","Curling leaves","Sticky leaves","Pale leaves","Drooping leaves","Sticky residue","Mosaic pattern","Sooty mold","Bleached leaves","Silver streaks on leaves"]},
        {"icon": "🌿", "label": "Stem Problems",           "symptoms": ["Wilting","Stem rot","Black stem","Leggy stem","Galls on stem","Brown bumps on stem"]},
        {"icon": "🌱", "label": "Root Problems",           "symptoms": ["Root rot","Smelly roots","Stunted growth","No growth"]},
        {"icon": "🌸", "label": "Flower / Fruit Problems", "symptoms": ["Flower drop","No flowers","Fruit rot","Small fruit","Bud drop"]},
        {"icon": "🐛", "label": "Pest Problems",           "symptoms": ["Spider mites","Fine webbing","Mealybugs","White cottony mass","Whiteflies","Thrips"]},
        {"icon": "🌡️","label": "Environmental Problems",  "symptoms": ["Sunburn","Frost damage","Wilting despite watering","Distorted leaves","Black after cold"]},
    ]

    if request.method == "POST":
        plant_name    = request.POST.get("plant_name", "").strip()
        symptoms_list = request.POST.getlist("symptoms")
        plant_image   = request.FILES.get("plant_image")

        if plant_name == "Other":
            plant_name = request.POST.get("plant_input", "").strip()
        if not plant_name:
            plant_name = "Unknown Plant"

        # Must select at least one symptom
        if not symptoms_list:
            return render(request, "diagnose.html", {
                "symptom_groups": symptom_groups,
                "error": "Please select at least one symptom."
            })

        disease, cure = get_diagnosis(symptoms_list)
        Diagnosis.objects.create(
            user=request.user,
            plant_name=plant_name,
            symptoms=", ".join(symptoms_list),
            disease=disease,
            cure=cure,
            plant_image=plant_image
        )
        return redirect("hh")

    return render(request, "diagnose.html", {"symptom_groups": symptom_groups})


@login_required(login_url='/login')
def mark_cured(request, pk):
    diagnosis = get_object_or_404(Diagnosis, pk=pk, user=request.user)
    diagnosis.is_cured = True
    diagnosis.save()
    messages.success(request, f"✅ {diagnosis.plant_name} marked as cured!")
    return redirect("hh")


@login_required(login_url='/login')
def profile_view(request):
    user    = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            full_name  = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split(" ", 1)
            user.first_name = name_parts[0]
            user.last_name  = name_parts[1] if len(name_parts) > 1 else ""
            user.email = form.cleaned_data['email']

            new_password     = form.cleaned_data.get('new_password')
            confirm_password = form.cleaned_data.get('confirm_password')
            if new_password:
                if new_password == confirm_password:
                    user.set_password(new_password)
                    update_session_auth_hash(request, user)
                else:
                    messages.error(request, "Passwords do not match.")
                    return redirect("profile")

            user.save()
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile, initial={
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "email":     user.email,
            "city":      profile.city or ""
        })

    return render(request, "profile.html", {"form": form})


@login_required(login_url='/login')
def hh_view(request):
    diagnoses = Diagnosis.objects.filter(user=request.user).order_by("-date")
    return render(request, "hh.html", {"diagnoses": diagnoses})


@login_required(login_url='/login')
def history_view(request):
    diagnoses = Diagnosis.objects.filter(user=request.user).order_by("-date")
    return render(request, "hh.html", {"diagnoses": diagnoses})


@login_required(login_url='/login')
def diagnosis_detail(request, pk):
    diagnosis = get_object_or_404(Diagnosis, pk=pk, user=request.user)
    return render(request, "diagnosis_detail.html", {"d": diagnosis})


@login_required(login_url='/login')
def diagnosis_pdf(request, pk):
    diagnosis = get_object_or_404(Diagnosis, pk=pk, user=request.user)

    buffer = io.BytesIO()
    p      = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header background
    p.setFillColorRGB(0.06, 0.63, 0.35)
    p.rect(0, height - 80, width, 80, fill=1, stroke=0)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(50, height - 50, "FloraCure — Diagnosis Report")
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 68, "Expert Plant Disease Diagnosis System")

    # Content
    p.setFillColorRGB(0, 0, 0)
    y = height - 120

    fields = [
        ("Plant Name", diagnosis.plant_name),
        ("Disease",    diagnosis.disease),
        ("Status",     "✓ Cured" if diagnosis.is_cured else "⏳ In Treatment"),
        ("Date",       diagnosis.date.strftime('%d %B %Y, %I:%M %p')),
    ]
    for label, value in fields:
        p.setFillColorRGB(0.06, 0.63, 0.35)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"{label}:")
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 12)
        p.drawString(180, y, str(value))
        y -= 28

    # Symptoms
    y -= 10
    p.setFillColorRGB(0.06, 0.63, 0.35)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Symptoms:")
    y -= 20
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    for sym in diagnosis.symptoms.split(", "):
        p.drawString(70, y, f"• {sym}")
        y -= 16

    # Cure
    y -= 10
    p.setFillColorRGB(0.06, 0.63, 0.35)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Recommended Cure:")
    y -= 20
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    cure_words, line = diagnosis.cure.split(), ""
    for word in cure_words:
        if len(line + word) < 80:
            line += word + " "
        else:
            p.drawString(70, y, line.strip())
            y -= 16
            line = word + " "
    if line:
        p.drawString(70, y, line.strip())

    # Footer
    p.setFillColorRGB(0.06, 0.63, 0.35)
    p.rect(0, 0, width, 35, fill=1, stroke=0)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, 12, "Generated by FloraCure Expert System  |  For informational purposes only")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="FloraCure_{diagnosis.plant_name}.pdf"'
    return response
