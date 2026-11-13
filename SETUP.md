# Setup: put this on your GitHub profile

Your GitHub profile README is the file `README.md` inside a repo named exactly like your username
(for example `hariom/hariom`). GitHub shows it at the top of your profile page.

## 1. Create the repo
1. On GitHub: **New repository**. Name it **exactly your username**. Make it **Public**.
2. Tick **Add a README file**, then create it.

## 2. Upload this folder
Upload everything in this folder into that repo, including the hidden `.github` folder
(on Windows/Mac you may need to turn on "show hidden files").

Easiest with git:

```
git clone https://github.com/YOUR_USERNAME/YOUR_USERNAME
# copy every file from this folder into the cloned folder, replacing README.md
cd YOUR_USERNAME
git add -A
git commit -m "Add animated profile"
git push
```

## 3. Edit `config.json`
- Replace `YOUR_LEETCODE_ID` and `YOUR_CODEFORCES_HANDLE` in the two `url` fields. The SOLVE and COMPETE tiles link there.
- Change the ratings, tagline or tags if you like. Leave `github_user` empty; the Action finds it by itself.
- To choose which repos appear, list their names in `"featured"`. Leave it empty to show your most-starred ones.

## 4. Turn the sample data into your real data
Open the **Actions** tab, pick **Update profile cards**, then **Run workflow**. After a minute it commits your real
contribution graph, streaks and repos, and from then on it refreshes every morning (06:00 IST).
Until it has run, the cards show a yellow **SAMPLE DATA** badge.

If the run cannot push, go to **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**.

## Notes
- The graph counts public contributions. To include private ones, turn on **Include private contributions on my profile** in your profile settings.
- Edit `README.template.md` to change the layout, not `README.md` (it gets regenerated).
- Want your own look in the hero? Replace `assets/portrait.txt` with any ASCII art (an image-to-ASCII tool works for a portrait).
- Preview on your computer: `python scripts/render_readme_cards.py` (add `STATIC=1` to see the final frame instead of the animation).
