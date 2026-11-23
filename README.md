# CAVE Clinic website

A fast, static website (plain HTML, CSS and JavaScript, with no frameworks), built from simple data files.

## How it fits together
```
data/        ← the words, prices, team, locations, reviews, events and journal posts (edit these)
images/      ← drop real photos and films here (see images/README.md for the names)
src/         ← the design (styles.css) and interactions (main.js)
build.py     ← turns all of the above into finished pages
site/        ← the finished website. Upload this folder to your host.
```

## Preview online (Netlify, free)
1. Sign in at https://app.netlify.com with your GitHub account.
2. Click **Add new site**, then **Import an existing project**, then choose GitHub and pick `cave-clinic-website`.
3. Leave **Build command** empty. Set **Publish directory** to `site`.
4. Click **Deploy**. You get a link like `something.netlify.app`, and it updates every time changes are pushed.

## Photos
The clinic photos, Paris's portrait, the ebook cover and the 4 before/after results come from caveclinic.uk, reused with Paris's permission.
`data/photos.json` holds each photo's alt text and focal point. Before/after photos are split into halves, left = before.
Results 1 and 3 show side by side (`"layout": "split"` in `data/results.json`) because the two halves don't line up for a slider.

## Make a change
1. Edit a file in `data/`. For example, change a price in `data/treatments.json`.
2. Rebuild:
```bash
python3 build.py
```
3. Preview at http://localhost:8000:
```bash
python3 -m http.server 8000 --directory site
```

The build stops with an error if a page title goes over 60 characters, a page has more than one H1, or a prescription-only medicine name appears. That's on purpose.

## Journal posts
Each post is a `.md` file in `data/journal/`. Copy one and change the top lines (title, date, category, image, alt, summary). Then write the post under the `---` line.
- `## ` starts a heading.
- `- ` starts a bullet point.
- `**bold**` makes text bold.

## Before going live
- **Forms:** the contact and Academy forms check the fields but don't send anywhere yet. Create a free form endpoint (for example Formspree), then put its URL in `formAction` in `data/site.json`.
- **Hosting:** upload the `site/` folder to Netlify, Cloudflare Pages or Vercel. They all serve `404.html` automatically. Point caveclinic.uk at it.
- **Search:** submit `https://caveclinic.uk/sitemap.xml` in Google Search Console.
- **Old site:** the Squarespace demo shop products (such as "Harvest Moon Cup") aren't carried over. Delete them in Squarespace, or simply cancel Squarespace once this site is live.

## Things to confirm with Paris (shown as [to confirm] on the site)
- City centre days: Wednesday and Sunday, or Sunday only (`data/locations.json`, set `toConfirm` to false when done)
- FAQ answers (The CAVE Secret page, in `build.py` under `FAQ`)
- Credentials and awards, by name (`data/paris.json`)
- Care and hygiene paragraph (The clinic page)
- Ebook price and summary (Academy page)
- Event dates (`data/events.json`)
- Treatment durations (`duration` in `data/treatments.json`, currently blank)
- Which review belongs with which result (`data/results.json`)
