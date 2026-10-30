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
]