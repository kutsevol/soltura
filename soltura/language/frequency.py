# Frequency bands from the most frequent lemmas to about B1; a learner who passes all
# of them gets everything up to 6,000 marked known. The placement test asks them, the
# vocabulary map draws them and reading measures a learner against them.
BANDS: tuple[tuple[int, int], ...] = (
    (1, 250),
    (251, 500),
    (501, 1000),
    (1001, 1500),
    (1501, 2000),
    (2001, 3000),
    (3001, 4500),
    (4501, 6000),
)

# The rank of a word the frequency seed never saw but a learner saved anyway.
UNRANKED = 1_000_000
