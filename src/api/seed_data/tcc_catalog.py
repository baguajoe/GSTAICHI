"""
Starting data for Tai Chi Company: site settings, tiers, plans and the placeholder video library.
Loaded by `flask seed-tcc`. Everything here can be changed later in /admin.
"""

DEFAULT_SITE_SETTINGS = {
    "app_name": "Tai Chi Company",
    "school_name": "Gin Soon Tai Chi Chuan Federation",
    "logo_url": None,
    "primary_color": "#590d0d",
    "contact_phone": "(617) 542-4442",
    "contact_email": "chu.v@usa.com",
    "address": "33 Harrison Avenue, 5th Floor, Boston, MA 02111",
    "notification_email": "chu.v@usa.com",
    "copyright_line": "Gin Soon Tai Chi Chuan Federation. All rights reserved.",
    "article_categories": [
        "Application", "Forms", "Health", "Masters", "Philosophy", "Power",
        "Push Hands", "Qigong", "Technique", "Weapons", "Other",
    ],
    "video_sections": [
        {"key": "beginner", "label": "Beginner", "tier_rank": 1},
        {"key": "intermediate", "label": "Intermediate", "tier_rank": 2},
        {"key": "advanced", "label": "Advanced", "tier_rank": 3},
        {"key": "qigong", "label": "Qigong", "tier_rank": 1},
    ],
    "terms_of_service_text": """These videos and articles are for your personal use only.

Your membership lets you watch the videos and read the articles yourself, on your own devices. You may not share your account, password or content with anyone else.

Recording, copying, downloading, screen-capturing, re-posting or sharing any video or article, in whole or in part, is strictly prohibited. Every video and article carries your name and member ID, so any copy can be traced back to the account it came from.

We may suspend or close accounts that break these rules, without a refund.

All videos, articles and images are protected by copyright and belong to the school.""",
}

TIERS = [
    {"name": "Beginner", "rank": 1, "sort_order": 1,
     "description": "All Beginner forms, the full Qigong section, and every member article.",
     "monthly": "9.99", "yearly": "99.00"},
    {"name": "Intermediate", "rank": 2, "sort_order": 2,
     "description": "Everything in Beginner, plus Intermediate forms, weapons and push hands.",
     "monthly": "14.99", "yearly": "149.00"},
    {"name": "Advanced", "rank": 3, "sort_order": 3,
     "description": "The complete library: everything in Intermediate, plus the Advanced forms.",
     "monthly": "19.99", "yearly": "199.00"},
]

SECTION_TIER_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3, "qigong": 1}

# slug = folder name in the R2 streams bucket
VIDEOS = [
    # BEGINNER
    {"slug": "fundamentals", "title": "Tai Chi Chuan Fundamentals", "section": "beginner", "category": "Fundamentals", "is_free_sample": True,
     "short_description": "Tai Chi Chuan is one of the treasures of China's heritage, with a long history and valuable merits in self-defense, performance, health maintenance, and personal growth. Rooted in Tai Chi Yin-Yang philosophy, Lao Tzu's teachings, traditional Chinese medicine, martial arts principles, and life-nurturing arts, it offers a comprehensive approach to well-being."},
    {"slug": "tai-chi-gong", "title": "Tai Chi Gong", "section": "beginner", "category": "Fundamentals",
     "short_description": "Tai Chi Chuan has become a popular health-maintenance exercise, but its solo form can be difficult for new students to learn. To address this, Tai Chi Gong was created with exercises that are easy to learn, simple to practice, and designed to help students gradually build their Tai Chi foundation."},
    {"slug": "10-large-circle", "title": "10 Techniques Large Circle Form", "section": "beginner", "category": "Forms",
     "short_description": "Due to physical limitations, Tai Chi Chuan movements use circular motions categorized as large, medium, or small. Large circles in Tai Chi Chuan emphasize expansive movement and flow, aiding in martial applications while supporting flexibility, strength, and broader body coordination."},
    {"slug": "18-medium-frame", "title": "18 Techniques Medium Frame Solo Form", "section": "beginner", "category": "Forms",
     "short_description": "Due to physical limitations, Tai Chi Chuan movements are categorized into circular motions of different sizes—large, medium, and small. The 18 Techniques Medium Frame Tai Chi Chuan solo form is an abbreviated version of the traditional Yang Style, based on the teachings of Yeung Sau Chung, focusing on precision, balance, and martial applications."},
    {"slug": "21-small-circle", "title": "21 Techniques Small Circle Form", "section": "beginner", "category": "Forms",
     "short_description": "Advanced small circle movements focusing on compact, efficient techniques."},
    {"slug": "15-small-frame", "title": "15 Techniques Small Solo Frame", "section": "beginner", "category": "Forms",
     "short_description": ""},
    {"slug": "chens-11", "title": "Chen's 11 Tai Chi Chuan Techniques", "section": "beginner", "category": "Forms",
     "short_description": "The 11 techniques Tai Chi Chuan is not an abbreviated form, but a collection of 11 essential techniques practiced individually. Created by Chen Wei Ming (1881-1958), this method focuses on fundamental movements and mastery of individual techniques rather than teaching a choreographed sequence for beginners."},
    {"slug": "11-techniques-aj", "title": "The 11 Techniques AJ Tai Chi Chuan", "section": "beginner", "category": "Forms",
     "short_description": ""},
    {"slug": "22-medium-frame", "title": "22 Techniques Medium Frame Tai Chi Chuan", "section": "beginner", "category": "Forms",
     "short_description": ""},
    # INTERMEDIATE
    {"slug": "34-small-circle", "title": "34 Techniques Small Circle Form", "section": "intermediate", "category": "Forms",
     "short_description": "Comprehensive small circle form with expanded techniques and applications."},
    {"slug": "12-returning", "title": "12 Techniques Returning Tai Chi Chuan Solo Form", "section": "intermediate", "category": "Forms",
     "short_description": ""},
    {"slug": "22-sword", "title": "22 Technique Tai Chi Sword Form", "section": "intermediate", "category": "Weapons",
     "short_description": "For its gracefulness in motion, Tai Chi Sword is one of the most popular weapons in the Tai Chi Chuan System. The 22 Techniques Tai Chi Sword form, developed from traditional Yang Style Tai Chi Sword, emphasizes softness, elasticity, dynamic stepping, coordination, and the principle of body and mind unity through four structured sections tailored for various levels and ages."},
    {"slug": "26-broadsword", "title": "26 Techniques Tai Chi Broadsword", "section": "intermediate", "category": "Weapons",
     "short_description": ""},
    {"slug": "push-hands", "title": "Tai Chi Chuan Push Hands Exercises", "section": "intermediate", "category": "Push Hands",
     "short_description": "Partner drill training in Chinese martial arts, including push hands exercises, is essential for understanding offensive and defensive techniques. Beginning with pre-programmed movements and progressing to randomized applications, push hands develop speed, power, and proper technique execution during combat simulations."},
    # ADVANCED
    {"slug": "yang-medium-frame-1", "title": "Yang Style Medium Frame Solo Form Part 1", "section": "advanced", "category": "Forms",
     "short_description": "Tai Chi Chuan is one of the great treasures of Chinese culture, practiced globally for health, fitness, and meditation. As a gentle exercise, Tai Chi suits all physical conditions and ages, making it a lifelong practice for wellness."},
    {"slug": "yang-medium-frame-2", "title": "Yang Style Medium Frame Solo Form Part 2", "section": "advanced", "category": "Forms",
     "short_description": "Tai Chi Chuan, with its slow and relaxed movements, is ideal for fitness, meditation, and health maintenance. Practitioners can benefit from its gentle physical nature from youth through old age, maintaining vitality and balance."},
    {"slug": "13-animals-1", "title": "13 Animals Form Part 1", "section": "advanced", "category": "Forms",
     "short_description": "Among the Tai Chi Chuan forms, the Tai Chi 13 Dan Shi, or 13 Animals Form, is the oldest known form. Known as the 13 Ways of Solidifying the Elixir, it preserves ancient Tai Chi techniques that many contemporary practitioners rarely explore, making it a true cornerstone of the practice."},
    {"slug": "13-animals-2", "title": "13 Animals Form Part 2", "section": "advanced", "category": "Forms",
     "short_description": "The Tai Chi 13 Animals Form continues with its rich exploration of the oldest Tai Chi Chuan techniques. As a rare form practiced today, it emphasizes internal energy cultivation and mastery of traditional movements, preserving the foundation of Tai Chi for future generations."},
    {"slug": "eight-zhan-zhuang", "title": "Internal Martial Art Eight Zhan Zhuang Techniques", "section": "advanced", "category": "Standing Exercises",
     "short_description": "The Internal Martial Art Eight Zhan Zhuang Techniques, also known as the universal stance, focus on both external support and internal qi circulation. Properly positioned stances enable the free flow of qi inside the body, promoting internal power accumulation through comfortable alignment and natural energy flow."},
    # QIGONG (every paying member, any tier)
    {"slug": "ba-duan-jin", "title": "Ba Duan Jin Qigong", "section": "qigong", "category": "Qigong",
     "short_description": "In ancient China, many people pursued self-tempering exercises to enhance their well-being and extend longevity. Over time, these efforts led to the development of Ba Duan Jin Qigong, a traditional set of exercises focused on improving health and promoting vitality through disciplined practice."},
    {"slug": "five-animals-frolics", "title": "Five Animals Frolics", "section": "qigong", "category": "Qigong",
     "short_description": "Five Animal Frolics is a famous Daoyin exercise created by Hua Tuo during the Eastern Han Dynasty to promote qi and blood circulation, inspired by the principle of constant movement to prevent stagnation and illness."},
]
