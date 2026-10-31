# Political question loading and text stems

The former entry imported six JSON modules containing about 17.1 MiB of text
and embedded Base64 WebP data, including every daily stem crop. On both live
publications this remained on the loading screen after 20 seconds at 200 KiB/s.

The six datasets now contain only question text and image paths. The 243 unique
WebP images were decoded without changing their bytes; their SHA-256 prefixes
form the public filenames. Proof images load only when the reader opens a
source-proof control. Both Sites' external image base and the GitHub Pages
repository subdirectory must remain supported.

All 149 daily-workbook stems are now text, with numbered blank markers. Original
question IDs and source-page references remain. Existing matching, judgement,
fill and self-review answers outside the daily workbook are byte-equivalent
after normalizing the image representation. The daily workbook remains pending
reference answers: conversion does not introduce an answer key or automatic
grading.

The reviewed text has 468 fill positions. The previous 488 input positions
included split cross-line blanks, two duplicated slots, and blanks left at the
top of the next crop. `legacyBlankSources` assigns every one of the old 488
positions exactly once to its actual question. In particular, Day29 question2's
last two blanks and Day30 question2's final blank no longer appear in question3.

`daily-text-v1` is a separate answer-storage revision. Migration copies filled
values and submission state to the new positions while retaining every original
storage entry. It is idempotent, does not change favourites or notes, and does
not overwrite already-edited text-version answers.

The loading screen allows switching to another subject, shows a slow-connection
message after 15 seconds, and offers a full-page retry. Reloading clears the
browser's failed dynamic-import state while keeping saved practice records.
Subject switching updates the current URL without changing its origin or base
path, so refreshing the political module stays in that subject.

The original political directory also required `Array.prototype.at`, which
is absent on older iPad browsers. Entry no longer requires that built-in,
and the migration avoids `Object.hasOwn` for the same compatibility reason.
