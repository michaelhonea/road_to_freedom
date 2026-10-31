# Setup (run it on your PC first)

## 1. Install
```
cd road_to_freedom
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
```
Edit `.env`: set `ADMIN_PASSWORD` and `SECRET_KEY`. Add `ANTHROPIC_API_KEY` to turn on the AI answers. Leave `SMS_DRY_RUN=true`.

## 2. Run
```
python main.py
```
Open http://127.0.0.1:8000. Leader login is at `/admin/login`.

## 3. First-time tasks
1. Admin > Members: add a group (e.g. "Thursday Night") and yourself as a member.
2. Admin > Daily Notes: add a note for today, then Admin > Send Text to test. In dry-run mode nothing is actually texted; check Admin > Message Log.
3. Admin > Meetings: add a meeting with a reminder time.
4. Visit `/ask` and try a question about the sample lessons.

## 4. The resource library (already imported)
The free Celebrate Recovery downloads are already built into this site:
- `/lessons`: all 25 lessons as web pages (text from the Leader's Guide) plus each lesson's notes PDF
- `/resources`: the 8 Principles, 12 Steps, inventory sheets, group guidelines, pamphlets, and one combined PDF of all lesson notes
- The AI question box answers from these lessons, the 8 Principles, 12 Steps, and Step Study Assignments

Files live in `src/static/resources/`, lesson text in `src/content/lessons/`, and the index in `src/content/resources.json`.

### Updating when Celebrate Recovery posts new versions
Download and unzip the new files from https://celebraterecovery.com/free-resources/, then:
```
pip install pypdf reportlab
python -m src.tools.import_resources --leader "<Lessons-from-Leaders-Guide folder>" --inserts "<Bulletin-Inserts folder>" --ministry "<MinistryDocs folder>" --pamphlets "<Issue-Pamphlets folder>"
```
This needs `pandoc` and `pdftotext` (poppler) installed. It replaces the imported lessons and files. Then commit and push to GitHub. (The admin "Reload lesson files" button reloads the lesson text and search index without restarting.)

### Adding your own Road to Freedom lessons
Add Markdown files to `src/content/lessons/` (one `# Title`, sections as `## Heading`). They are searchable by the AI box right away. Note: the importer clears that folder, so keep your own lessons in `src/content/lessons/` only after running an import, or back them up first.

## 5. Optional: your own PDF workbook
`python -m src.tools.build_pdf` (needs `pip install weasyprint`) builds one PDF from all Markdown lessons in `src/content/lessons/`. Output: `build/Road_to_Freedom_Workbook.pdf`.

## Credit and permission
These materials come from Celebrate Recovery's free resources page, which asks ministries to use only its approved versions. The files are shown unmodified with credit on each page. The page states no license terms, so email Celebrate Recovery to confirm you may host them on your ministry's site.

## Troubleshooting
- Port busy: change the port in `main.py`.
- No AI answers: confirm `ANTHROPIC_API_KEY`; without it the box shows the closest lesson text only.
- Texts not sending: check `SMS_DRY_RUN`, the Message Log status column, and that the member is opted in.
