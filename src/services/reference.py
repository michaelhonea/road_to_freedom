"""Static reference content shown on the home, Principles & Steps, and Meetings pages.

Meeting details live here so they are easy to change in one place.
"""
from . import library

MEETING = {
    "day": "Every Sunday",
    "time": "6:00 PM",
    "place": "New Covenant Church of God",
    "street": "304 S Pine St",
    "city": "Summerville, SC 29483",
    "maps_url": "https://maps.google.com/?q=304+S+Pine+St+Summerville+SC+29483",
    "embed_url": "https://maps.google.com/maps?q=304+S+Pine+St,+Summerville,+SC+29483&output=embed&z=15",
    "welcome": "Men and women welcome. No sign-up needed. Just show up.",
    "format": ["Prayer", "Teaching", "Open share"],
    "promise": ["Safe", "Confidential", "Christ-centered"],
    "church_url": "https://www.newcovenantcog.com/",
    "church_phone": "(843) 569-7691",
    "church_email": "info@newcovenantcog.com",
}

# Celebrate Recovery(R) 8 Principles, each tied to its Beatitude and Step(s).
PRINCIPLES = [
    {"num": 1, "key": "Realize", "steps": "1",
     "text": "Realize I'm not God. I admit that I am powerless to control my tendency to do the wrong thing and that my life is unmanageable.",
     "verse": "Blessed are the poor in spirit, for theirs is the kingdom of heaven.", "ref": "Matthew 5:3"},
    {"num": 2, "key": "Earnestly believe", "steps": "2",
     "text": "Earnestly believe that God exists, that I matter to Him and that He has the power to help me recover.",
     "verse": "Blessed are those who mourn, for they will be comforted.", "ref": "Matthew 5:4"},
    {"num": 3, "key": "Consciously choose", "steps": "3",
     "text": "Consciously choose to commit all my life and will to Christ's care and control.",
     "verse": "Blessed are the meek, for they will inherit the earth.", "ref": "Matthew 5:5"},
    {"num": 4, "key": "Openly examine", "steps": "4 and 5",
     "text": "Openly examine and confess my hurts, hang-ups and habits to myself, to God, and to someone I trust.",
     "verse": "Blessed are the pure in heart, for they will see God.", "ref": "Matthew 5:8"},
    {"num": 5, "key": "Voluntarily submit", "steps": "6 and 7",
     "text": "Voluntarily submit to any and all changes God wants to make in my life and humbly ask Him to remove my character defects.",
     "verse": "Blessed are those who hunger and thirst for righteousness, for they will be filled.", "ref": "Matthew 5:6"},
    {"num": 6, "key": "Evaluate all relationships", "steps": "8 and 9",
     "text": "Evaluate all my relationships. Offer forgiveness to those who have hurt me and make amends for harm I've done to others when possible, except when to do so would harm them or others.",
     "verse": "Blessed are the merciful, for they will be shown mercy.", "ref": "Matthew 5:7",
     "verse2": "Blessed are the peacemakers, for they will be called children of God.", "ref2": "Matthew 5:9"},
    {"num": 7, "key": "Reserve a daily time", "steps": "10 and 11",
     "text": "Reserve a daily time with God for self-examination, Bible reading, and prayer in order to know God and His will for my life and to gain the power to follow His will.",
     "verse": "", "ref": ""},
    {"num": 8, "key": "Yield", "steps": "12",
     "text": "Yield myself to God to be used to bring this Good News to others, both by my example and my words.",
     "verse": "Blessed are those who are persecuted because of righteousness, for theirs is the kingdom of heaven.", "ref": "Matthew 5:10"},
]

STEPS = [
    (1, "We admitted we were powerless over our addictions and compulsive behaviors, that our lives had become unmanageable.", "Romans 7:18"),
    (2, "We came to believe that a power greater than ourselves could restore us to sanity.", "Philippians 2:13"),
    (3, "We made a decision to turn our lives and our wills over to the care of God.", "Romans 12:1"),
    (4, "We made a searching and fearless moral inventory of ourselves.", "Lamentations 3:40"),
    (5, "We admitted to God, to ourselves, and to another human being the exact nature of our wrongs.", "James 5:16"),
    (6, "We were entirely ready to have God remove all these defects of character.", "James 4:10"),
    (7, "We humbly asked Him to remove all our shortcomings.", "1 John 1:9"),
    (8, "We made a list of all persons we had harmed and became willing to make amends to them all.", "Luke 6:31"),
    (9, "We made direct amends to such people whenever possible, except when to do so would injure them or others.", "Matthew 5:23-24"),
    (10, "We continued to take personal inventory and when we were wrong, promptly admitted it.", "1 Corinthians 10:12"),
    (11, "We sought through prayer and meditation to improve our conscious contact with God, praying only for knowledge of His will for us, and power to carry that out.", "Colossians 3:16"),
    (12, "Having had a spiritual experience as the result of these steps, we try to carry this message to others and practice these principles in all our affairs.", "Galatians 6:1"),
]

STEP_TEXT = [{"num": n, "text": t, "ref": r} for n, t, r in STEPS]


def principles_with_lessons() -> list[dict]:
    """Each principle plus the lessons the library has filed under it."""
    by_p: dict[int, list[dict]] = {}
    for lsn in library.lessons():
        if lsn.get("principle"):
            by_p.setdefault(lsn["principle"], []).append(lsn)
    return [dict(p, lessons=by_p.get(p["num"], [])) for p in PRINCIPLES]


def extra_lessons() -> list[dict]:
    return [l for l in library.lessons() if not l.get("principle")]
