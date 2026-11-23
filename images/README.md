# Photos and films for the CAVE Clinic site

Put files in this folder with exactly these names, then run `python3 build.py` again.
Each beige placeholder on the site turns into the real photo automatically.

- Photos: **.webp** is best (smaller, faster). .jpg also works. Aim for 2400px wide, under 400 KB.
- Films: **.mp4**, muted, 8 to 20 seconds, under 8 MB.
- Use CAVE's own photos and consented client images only. No stock faces.
- Grade every image the same way: warm and neutral, with soft daylight.

## Home page
| File name | What it shows |
|---|---|
| hero.mp4 + hero-poster.webp | Slow walk past the sheer curtains, bouclé chairs and marble table into the treatment room |
| walk-arrival.webp | 01 The arrival: curtains, bouclé chairs, marble table |
| walk-lounge.webp | 02 The lounge: chocolate bouclé sofa, candles |
| walk-suite.mp4 + walk-suite.webp | 03 The treatment suite (muted loop + still) |
| walk-suite-full.mp4 | Optional: the same film with sound, for "Play with sound" |
| walk-details.webp | 04 The details: brass wall lights, plaster art, CAVE menu |
| paris-portrait.webp | Tall 4:5 portrait of Paris (shown in the arch) |
| paris-at-work.webp | Smaller photo of Paris working |
| find-lounge.webp | The lounge (Find us section and 404 page) |
| final-table.webp | The candlelit marble table (final call to action) |

## Treatments (hover previews and mobile thumbnails, 4:5)
treat-facial-balancing · treat-lips · treat-skin-boosters · treat-facials · treat-body · treat-anti-wrinkle · treat-wellbeing · treat-consultation

## Results (consented images only, 4:5)
result-1-before / result-1-after … up to result-6-before / result-6-after.
Match each pair to the treatment and review in `data/results.json`.

## Team, events, other pages
- team-paris, team-alix (3:4 portraits)
- event-galentines, event-wellness, event-london (3:2 landscape)
- secret-hero (profile close-up for The CAVE Secret page)
- tour.mp4 + tour-poster.webp, tour-full.mp4 (clinic tour with sound)
- clinic-entrance
- paris-work-1, paris-work-2, paris-work-3
- menu-1 to menu-4 (small strip in the mobile menu)
- journal-facial-balancing, journal-ethics, journal-facial-secrets, journal-home-salon, journal-media, journal-skin-boosters

## Share image
`src/og/og-default.jpg` is the picture shown when the site is shared (1200x630). It's currently the wordmark on ivory. Swap it for a 1200x630 photo of the lounge with the same file name.
