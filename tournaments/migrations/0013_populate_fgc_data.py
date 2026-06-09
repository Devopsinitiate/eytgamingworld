from django.db import migrations


SF6_CHARACTERS = [
    ("Ryu", "ryu", 1), ("Luke", "luke", 2), ("Jamie", "jamie", 3),
    ("Chun-Li", "chun-li", 4), ("Guile", "guile", 5), ("Kimberly", "kimberly", 6),
    ("Juri", "juri", 7), ("Ken", "ken", 8), ("Blanka", "blanka", 9),
    ("Dhalsim", "dhalsim", 10), ("E. Honda", "e-honda", 11),
    ("Dee Jay", "dee-jay", 12), ("Manon", "manon", 13),
    ("Marisa", "marisa", 14), ("JP", "jp", 15), ("Zangief", "zangief", 16),
    ("Lily", "lily", 17), ("Cammy", "cammy", 18), ("Rashid", "rashid", 19),
    ("A.K.I.", "aki", 20), ("Ed", "ed", 21), ("Akuma", "akuma", 22),
    ("M. Bison", "m-bison", 23), ("Terry Bogard", "terry-bogard", 24),
    ("Mai Shiranui", "mai-shiranui", 25),
]

SF6_STAGES = [
    ("Training Room", "training-room"),
    ("Colosseo", "colosseo"),
    ("Metro City Downtown", "metro-city-downtown"),
    ("Genbu Temple", "genbu-temple"),
    ("Carrier Byron Taylor", "carrier-byron-taylor"),
    ("Tian Hong Yuan", "tian-hong-yuan"),
    ("Fête Foraine", "fete-foraine"),
    ("Old Town Bazaar", "old-town-bazaar"),
    ("Suval'hal Arena", "suvalhal-arena"),
    ("Machogan", "machogan"),
    ("The Macho Ring", "macho-ring"),
    ("Barmal Star", "barmal-star"),
    ("Beach of Glory", "beach-of-glory"),
    ("Enma's Hollow", "enmas-hollow"),
    ("Merchant's Carnival", "merchants-carnival"),
    ("Ruined Lab", "ruined-lab"),
]

MK1_CHARACTERS = [
    ("Johnny Cage", "johnny-cage", 1),
    ("Kenshi", "kenshi", 2),
    ("Kitana", "kitana", 3),
    ("Liu Kang", "liu-kang", 4),
    ("Mileena", "mileena", 5),
    ("Raiden", "raiden", 6),
    ("Scorpion", "scorpion", 7),
    ("Shang Tsung", "shang-tsung", 8),
    ("Sindel", "sindel", 9),
    ("Smoke", "smoke", 10),
    ("Sub-Zero", "sub-zero", 11),
    ("Ashrah", "ashrah", 12),
    ("Baraka", "baraka", 13),
    ("General Shao", "general-shao", 14),
    ("Geras", "geras", 15),
    ("Havik", "havik", 16),
    ("Li Mei", "li-mei", 17),
    ("Nitara", "nitara", 18),
    ("Rain", "rain", 19),
    ("Reiko", "reiko", 20),
    ("Reptile", "reptile", 21),
    ("Sareena", "sareena", 22),
    ("Tanya", "tanya", 23),
    ("Ermac", "ermac", 24),
    ("Homelander", "homelander", 25),
    ("Omni-Man", "omni-man", 26),
    ("Peacemaker", "peacemaker", 27),
    ("Ghostface", "ghostface", 28),
    ("Cyrax", "cyrax", 29),
    ("Sektor", "sektor", 30),
    ("Noob Saibot", "noob-saibot", 31),
    ("T-1000", "t-1000", 32),
]

MK1_STAGES = [
    ("Battle Dome", "battle-dome"),
    ("Crown Courtyard", "crown-courtyard"),
    ("Cyromancy Temple", "cryomancy-temple"),
    ("Fengjian Village", "fengjian-village"),
    ("Fire Temple", "fire-temple"),
    ("Fortress of Dominion", "fortress-of-dominion"),
    ("Havik's Citadel", "haviks-citadel"),
    ("Jailhouse", "jailhouse"),
    ("Living Forest", "living-forest"),
    ("Mileena's Throne Room", "mileenas-throne-room"),
    ("Muramasa", "muramasa"),
    ("Omega Island", "omega-island"),
    ("Orb of Tirith", "orb-of-tirith"),
    ("Outworld Palace", "outworld-palace"),
    ("Penthouse", "penthouse"),
    ("Shrine of the Fallen", "shrine-of-the-fallen"),
    ("Sky Temple", "sky-temple"),
    ("Slaughterhouse", "slaughterhouse"),
    ("Summit", "summit"),
    ("Sun Do Festival", "sun-do-festival"),
    ("The Forest", "the-forest"),
    ("The Mountain Pass", "the-mountain-pass"),
    ("Umgadi Palace", "umgadi-palace"),
    ("Wastelands", "wastelands"),
    ("Ying Fortress", "ying-fortress"),
]


def populate_fgc_data(apps, schema_editor):
    Game = apps.get_model("core", "Game")
    FGCGame = apps.get_model("tournaments", "FGCGame")
    Character = apps.get_model("tournaments", "Character")
    Stage = apps.get_model("tournaments", "Stage")

    for game_name, game_slug in [("Street Fighter 6", "sf6"), ("MK1", "mk1")]:
        try:
            game = Game.objects.get(slug=game_slug)
        except Game.DoesNotExist:
            continue

        FGCGame.objects.get_or_create(
            game=game,
            defaults={
                "default_best_of": 3,
                "supports_character_select": True,
                "supports_stage_select": True,
                "max_players_per_match": 2,
            },
        )

        chars = SF6_CHARACTERS if game_slug == "sf6" else MK1_CHARACTERS
        stages = SF6_STAGES if game_slug == "sf6" else MK1_STAGES

        for name, slug, order in chars:
            Character.objects.get_or_create(
                game=game, slug=slug, defaults={"name": name, "order": order}
            )

        for name, slug in stages:
            Stage.objects.get_or_create(
                game=game, slug=slug, defaults={"name": name}
            )


def reverse_populate(apps, schema_editor):
    Game = apps.get_model("core", "Game")
    FGCGame = apps.get_model("tournaments", "FGCGame")
    Character = apps.get_model("tournaments", "Character")
    Stage = apps.get_model("tournaments", "Stage")

    for game_name, game_slug in [("Street Fighter 6", "sf6"), ("MK1", "mk1")]:
        try:
            game = Game.objects.get(slug=game_slug)
        except Game.DoesNotExist:
            continue
        FGCGame.objects.filter(game=game).delete()
        Character.objects.filter(game=game).delete()
        Stage.objects.filter(game=game).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0012_fgc_models"),
    ]

    operations = [
        migrations.RunPython(populate_fgc_data, reverse_populate),
    ]
