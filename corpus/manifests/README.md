# Corpus manifests

Owner: Person 4. Store source metadata and rights records here.

`sources.json` indexes the English technique passages in `corpus/documents/`. Both underlying guides are CC BY-SA 4.0, so the translations are stored with attribution and the same license. Each record has source version `en-1`, audience, skill level, body-region tags, and the original PDF page locator. Clear contact, clear recovery, drop, smash, and the high serve are separate records so a clear arm-extension query cannot retrieve smash, drop, or serve text.

`excluded.json` lists sources that were reviewed and not copied: Waddell and Gowitzke 2000, the Zhou, Imai, and Ren clear paper, the Badminton England hitting sheet, Badminton Bible, and the BWF Level 2 coach manual. Those records have no text file and `review_status` `rejected`.

Original PDFs stay in gitignored `data/corpus-src/`. Do not commit them.
