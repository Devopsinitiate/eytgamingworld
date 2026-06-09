from django.db import migrations


T8_CHARACTERS = [
    ("Jin Kazama", "jin-kazama", 1), ("Kazuya Mishima", "kazuya-mishima", 2),
    ("Jun Kazama", "jun-kazama", 3), ("Paul Phoenix", "paul-phoenix", 4),
    ("Marshall Law", "marshall-law", 5), ("King", "king", 6),
    ("Lars Alexandersson", "lars-alexandersson", 7), ("Jack-8", "jack-8", 8),
    ("Nina Williams", "nina-williams", 9), ("Asuka Kazama", "asuka-kazama", 10),
    ("Ling Xiaoyu", "ling-xiaoyu", 11), ("Hwoarang", "hwoarang", 12),
    ("Bryan Fury", "bryan-fury", 13), ("Steve Fox", "steve-fox", 14),
    ("Yoshimitsu", "yoshimitsu", 15), ("Raven", "raven", 16),
    ("Azucena", "azucena", 17), ("Victor Chevalier", "victor-chevalier", 18),
    ("Reina", "reina", 19), ("Leo Kliesen", "leo-kliesen", 20),
    ("Sergei Dragunov", "sergei-dragunov", 21), ("Feng Wei", "feng-wei", 22),
    ("Kuma", "kuma", 23), ("Panda", "panda", 24),
    ("Claudio Serafino", "claudio-serafino", 25), ("Lee Chaolan", "lee-chaolan", 26),
    ("Alisa Bosconovitch", "alisa-bosconovitch", 27), ("Zafina", "zafina", 28),
    ("Leroy Smith", "leroy-smith", 29), ("Eddy Gordo", "eddy-gordo", 30),
    ("Lidia Sobieska", "lidia-sobieska", 31), ("Heihachi Mishima", "heihachi-mishima", 32),
    ("Shaheen", "shaheen", 33), ("Devil Jin", "devil-jin", 34),
    ("Clive Rosfield", "clive-rosfield", 35),
]

T8_STAGES = [
    ("Urban Square", "urban-square"), ("Yakushima", "yakushima"),
    ("Arena", "arena"), ("Coliseum of Fate", "coliseum-of-fate"),
    ("Descent into Subconscious", "descent-into-subconscious"),
    ("Sanctum", "sanctum"), ("Rebel Hangar", "rebel-hangar"),
    ("Dragon's Nest", "dragons-nest"), ("Okinawa", "okinawa"),
    ("Midnight Siege", "midnight-siege"), ("Pioneer", "pioneer"),
    ("Seaside Resort", "seaside-resort"), ("Celestial Gardens", "celestial-gardens"),
    ("Elegant Palace", "elegant-palace"), ("Acid Rain", "acid-rain"),
    ("Fallen Destiny", "fallen-destiny"),
]

STRIVE_CHARACTERS = [
    ("Sol Badguy", "sol-badguy", 1), ("Ky Kiske", "ky-kiske", 2),
    ("May", "may", 3), ("Axl Low", "axl-low", 4),
    ("Chipp Zanuff", "chipp-zanuff", 5), ("Potemkin", "potemkin", 6),
    ("Faust", "faust", 7), ("Millia Rage", "millia-rage", 8),
    ("Zato-1", "zato-1", 9), ("Ramlethal Valentine", "ramlethal-valentine", 10),
    ("Leo Whitefang", "leo-whitefang", 11), ("Nagoriyuki", "nagoriyuki", 12),
    ("Giovanna", "giovanna", 13), ("Anji Mito", "anji-mito", 14),
    ("I-No", "i-no", 15), ("Goldlewis Dickinson", "goldlewis-dickinson", 16),
    ("Jack-O", "jack-o", 17), ("Happy Chaos", "happy-chaos", 18),
    ("Baiken", "baiken", 19), ("Testament", "testament", 20),
    ("Bridget", "bridget", 21), ("Sin Kiske", "sin-kiske", 22),
    ("Bedman?", "bedman", 23), ("Asuka R.", "asuka-r", 24),
    ("Johnny", "johnny", 25), ("Elphelt Valentine", "elphelt-valentine", 26),
    ("A.B.A.", "aba", 27), ("Slayer", "slayer", 28),
    ("Dizzy", "dizzy", 29), ("Unika", "unika", 30),
]

STRIVE_STAGES = [
    ("Juno's Aria", "junos-aria"), ("Fiery Seeker's Passage", "fiery-seekers-passage"),
    ("L'Heure de la Fete", "lheure-de-la-fete"), ("Seaside Town", "seaside-town"),
    ("The Vanguard", "the-vanguard"), ("The Clawed Dawn", "the-clawed-dawn"),
    ("The Misadventure", "the-misadventure"), ("First Strike", "first-strike"),
    ("Despair of the Fettered", "despair-of-the-fettered"),
    ("Dawn of the Swords", "dawn-of-the-swords"), ("Cradle of Sin", "cradle-of-sin"),
    ("The Grand Retort", "the-grand-retort"), ("Heavenly Potemkin Buster", "heavenly-potemkin-buster"),
    ("The World of Shadows", "the-world-of-shadows"), ("Magical City", "magical-city"),
    ("The Devil's Aria", "the-devils-aria"), ("Dragon's Space", "dragons-space"),
    ("Forest of the Dead", "forest-of-the-dead"), ("Riverside Paradise", "riverside-paradise"),
    ("Soul of Chaos", "soul-of-chaos"),
]


def populate_fgc_data_t8_strive(apps, schema_editor):
    Game = apps.get_model("core", "Game")
    FGCGame = apps.get_model("tournaments", "FGCGame")
    Character = apps.get_model("tournaments", "Character")
    Stage = apps.get_model("tournaments", "Stage")
    ContentType = apps.get_model("contenttypes", "ContentType")

    for game_name, game_slug, genre in [
        ("Tekken 8", "tekken-8", "fighting"),
        ("Guilty Gear Strive", "guilty-gear-strive", "fighting"),
    ]:
        game, created = Game.objects.get_or_create(
            slug=game_slug,
            defaults={"name": game_name, "genre": genre, "category": "Fighting"},
        )
        if created:
            print(f"  Created Game: {game_name}")

        FGCGame.objects.get_or_create(
            game=game,
            defaults={
                "default_best_of": 3,
                "supports_character_select": True,
                "supports_stage_select": True,
                "max_players_per_match": 2,
            },
        )

        chars = T8_CHARACTERS if game_slug == "tekken-8" else STRIVE_CHARACTERS
        stages = T8_STAGES if game_slug == "tekken-8" else STRIVE_STAGES

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

    for game_name, game_slug in [
        ("Tekken 8", "tekken-8"),
        ("Guilty Gear Strive", "guilty-gear-strive"),
    ]:
        try:
            game = Game.objects.get(slug=game_slug)
        except Game.DoesNotExist:
            continue
        FGCGame.objects.filter(game=game).delete()
        Character.objects.filter(game=game).delete()
        Stage.objects.filter(game=game).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0013_populate_fgc_data"),
    ]

    operations = [
        migrations.RunPython(populate_fgc_data_t8_strive, reverse_populate),
    ]
