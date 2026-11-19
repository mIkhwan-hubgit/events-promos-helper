from clock import today

THIS_YEAR = today().year

SOURCES = [
    {
        "name": "POPULAR",
        "category": "bookstore_promo",
        "type": "html",
        "url": "https://www.popular.com.my/ongoing-promotions/",
    },
    {
        "name": "Kinokuniya",
        "category": "bookstore_promo",
        "type": "feed",
        "url": "https://kinokuniya.com.my/blogs/on-promotion.atom",
    },
    {
        "name": "BookXcess",
        "category": "bookstore_promo",
        "type": "html",
        "url": "https://www.bookxcess.com/",
    },
    {
        "name": "Big Bad Wolf",
        "category": "bookstore_promo",
        "type": "feed",
        "url": "https://www.bigbadwolfbooks.com/blogs/news.atom",
    },
    {
        "name": "DevMalaysia",
        "category": "tech_event",
        "type": "ical",
        "url": "https://api.luma.com/ics/get?entity=calendar&id=cal-6WejKZGvSfC5jo6",
    },
    {
        "name": "Luma KL",
        "category": "tech_event",
        "type": "ical",
        "tech_filter": True,  # mixed feed: ask Gemini which events are tech
        "url": "https://api.luma.com/ics/get?entity=discover&id=discplace-O15L1VZiYe0GYGm",
    },
    {
        "name": "dev.events",
        "category": "tech_event",
        "type": "jsonld",
        "region": "Malaysia",
        "url": "https://dev.events/meetups/AS/MY/Kuala_Lumpur",
    },
        {
        "name": "Malaysian AI",
        "category": "tech_event",
        "type": "ical",
        "tech_filter": True,
        "url": "https://api.luma.com/ics/get?entity=calendar&id=cal-pPgkuwCFrycSv1Z",
    },
        {
        "name": "CloudJoi",
        "category": "orchestra",
        "categories": ["orchestra", "workshop", "video_games"],  # one source, two tabs
        "type": "cloudjoi",
        "classify": True,
        "url": "https://www.cloudjoi.com/",
    },
    *[  # this season and next; the page for a new year is picked up automatically
        {
            "name": "MPO",
            "category": "orchestra",
            "type": "concert_page",
            "venue": "Dewan Filharmonik Petronas, KLCC",
            "url": f"https://www.mpo.com.my/season-{year}",
        }
        for year in (THIS_YEAR, THIS_YEAR + 1)
    ],
    {
        "name": "Malaysia What's On",
        "category": "orchestra",
        "categories": ["orchestra", "workshop", "video_games"],
        "type": "mwo",
        "classify": True,
        "url": "https://malaysiawhatson.com/events/",
    },
]