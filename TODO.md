# To do

## Quizzes give the answer away (found 2026-10-04)
- **Right after 잡기!** `battle([w])` asks a fill-in-the-blank whose options are the word just caught plus 2 others. The player saw that word a
  second ago, so it can't be failed and tests nothing. Replace it with a meaning check: the sentence with the word highlighted, then "이 문장에서
  'X'는 무슨 뜻이에요?" with 3 short Korean definitions. The first real cloze should come in 풀숲 after the spacing delay.
- **Wrong options are usually words never caught** (`distractors()` draws from the whole deck), so in review the one familiar option is the
  answer. Draw distractors from words already caught (same category, verb-ness, similar length), and fall back to the deck only while
  fewer than 2 are caught.
- **Optional:** after a scene, a short 쪽지 시험 over the words just caught, used as each other's distractors.
