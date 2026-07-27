# Viral Radar — GitHub Setup (No Coding Zaroori Nahi)

Yeh guide follow karke tool GitHub par khud chalega aur live website ban jayegi —
aapko apne computer pe kuch install ya chalane ki zaroorat nahi.

---

## Step 1: GitHub Account Banayein
1. https://github.com par jayein
2. "Sign up" par click karke free account banayein

## Step 2: Naya Repository Banayein
1. Upar right corner mein "+" icon > "New repository"
2. Naam dein: `viral-radar` (ya koi bhi naam)
3. **Public** select karein (Pages free sirf public repos ke liye kaam karta hai)
4. "Create repository" par click karein

## Step 3: Files Upload Karein
1. Repository page par "Add file" > "Upload files" par click karein
2. Yeh saari files/folders is zip mein hain — sabko drag-and-drop karein:
   - `index.html`
   - `viral_radar.py`
   - `requirements.txt`
   - `.github/workflows/scan.yml` (folder structure automatically bane rakhein)
3. Neeche "Commit changes" par click karein

**Zaroori:** `.github` folder ka naam waisa hi rakhein (dot ke sath) — yeh GitHub Actions ke liye zaroori hai.

## Step 4: Apni YouTube API Key "Secret" Ke Taur Par Daalein
(Yeh safe jagah hai — koi dekh nahi sakta)
1. Repo ke andar "Settings" tab par jayein
2. Left menu mein "Secrets and variables" > "Actions"
3. "New repository secret" par click karein
4. Name: `YOUTUBE_API_KEY`
5. Value: apni copy ki hui YouTube API key paste karein
6. "Add secret" par click karein

## Step 5: GitHub Pages On Karein (Live Website Banane Ke Liye)
1. "Settings" > left menu mein "Pages"
2. "Branch" ke neeche `main` select karein, folder `/ (root)` rakhein
3. "Save" par click karein
4. Kuch second baad upar ek link milega jaisay:
   `https://yourusername.github.io/viral-radar/`
   Yehi aapki live dashboard link hai.

## Step 6: Pehli Scan Manually Chalayein
1. Repo ke andar "Actions" tab par jayein
2. "Viral Radar Daily Scan" workflow par click karein
3. Right side "Run workflow" button dabayein > phir dobara "Run workflow" confirm karein
4. 1-2 minute wait karein — yeh khud data nikal kar `viral_radar_output.json` file repo mein save kar dega

## Step 7: Live Dashboard Dekhein
Step 5 wali link kholein — ab real data dikhega.

---

## Uske Baad Kya Hoga?
- Yeh workflow **roz khud chalega** (6:00 AM UTC) — aapko kuch nahi karna
- Har roz naye channels ka data update hota rahega
- Bas Step 7 wali link kabhi bhi kholein, naya data mil jayega

## Agar Kuch Ghalat Ho To
- **Actions tab mein red ❌ nazar aaye** → us par click karke error dekhein; zyada tar wajah galat API key hoti hai (Step 4 dobara check karein)
- **quotaExceeded error** → free daily quota khatam ho gaya, kal khud dobara chalega
- **Website purani dikh rahi** → Step 6 dobara manually chalayein
