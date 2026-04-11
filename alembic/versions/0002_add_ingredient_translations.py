"""add ingredient_translations table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Translations keyed by canonical English ingredient name.
# Each value is (fr_name, de_name, nl_name).
TRANSLATIONS: dict[str, tuple[str, str, str]] = {
    # Vegetables
    "onion": ("oignon", "Zwiebel", "ui"),
    "garlic": ("ail", "Knoblauch", "knoflook"),
    "tomato": ("tomate", "Tomate", "tomaat"),
    "carrot": ("carotte", "Karotte", "wortel"),
    "potato": ("pomme de terre", "Kartoffel", "aardappel"),
    "sweet potato": ("patate douce", "Süßkartoffel", "zoete aardappel"),
    "bell pepper": ("poivron", "Paprika", "paprika"),
    "zucchini": ("courgette", "Zucchini", "courgette"),
    "eggplant": ("aubergine", "Aubergine", "aubergine"),
    "broccoli": ("brocoli", "Brokkoli", "broccoli"),
    "cauliflower": ("chou-fleur", "Blumenkohl", "bloemkool"),
    "spinach": ("épinard", "Spinat", "spinazie"),
    "kale": ("chou frisé", "Grünkohl", "boerenkool"),
    "lettuce": ("laitue", "Kopfsalat", "sla"),
    "cucumber": ("concombre", "Gurke", "komkommer"),
    "celery": ("céleri", "Sellerie", "selderij"),
    "leek": ("poireau", "Lauch", "prei"),
    "mushroom": ("champignon", "Pilz", "paddenstoel"),
    "peas": ("petits pois", "Erbsen", "erwten"),
    "corn": ("maïs", "Mais", "maïs"),
    "green beans": ("haricots verts", "grüne Bohnen", "sperziebonen"),
    "asparagus": ("asperge", "Spargel", "asperge"),
    "pumpkin": ("citrouille", "Kürbis", "pompoen"),
    "cabbage": ("chou", "Kohl", "kool"),
    "beetroot": ("betterave", "Rote Bete", "rode biet"),
    "radish": ("radis", "Radieschen", "radijs"),
    # Fruits
    "lemon": ("citron", "Zitrone", "citroen"),
    "lime": ("citron vert", "Limette", "limoen"),
    "orange": ("orange", "Orange", "sinaasappel"),
    "apple": ("pomme", "Apfel", "appel"),
    "banana": ("banane", "Banane", "banaan"),
    "avocado": ("avocat", "Avocado", "avocado"),
    "strawberry": ("fraise", "Erdbeere", "aardbei"),
    "blueberry": ("myrtille", "Blaubeere", "bosbes"),
    "raspberry": ("framboise", "Himbeere", "framboos"),
    "mango": ("mangue", "Mango", "mango"),
    "pineapple": ("ananas", "Ananas", "ananas"),
    "peach": ("pêche", "Pfirsich", "perzik"),
    "pear": ("poire", "Birne", "peer"),
    "cherry": ("cerise", "Kirsche", "kers"),
    "grape": ("raisin", "Weintraube", "druif"),
    "coconut": ("noix de coco", "Kokosnuss", "kokosnoot"),
    # Meat
    "chicken breast": ("blanc de poulet", "Hähnchenbrust", "kipfilet"),
    "chicken thigh": ("cuisse de poulet", "Hähnchenschenkel", "kippendij"),
    "ground beef": ("bœuf haché", "Rinderhackfleisch", "rundergehakt"),
    "beef steak": ("steak de bœuf", "Rindersteak", "biefstuk"),
    "pork chop": ("côtelette de porc", "Schweinekotelett", "varkenskotelet"),
    "bacon": ("lardons", "Speck", "spek"),
    "lamb shoulder": ("épaule d'agneau", "Lammschulter", "lamsbout"),
    "sausage": ("saucisse", "Wurst", "worst"),
    "ham": ("jambon", "Schinken", "ham"),
    "turkey breast": ("blanc de dinde", "Putenbrust", "kalkoenfilet"),
    "duck breast": ("magret de canard", "Entenbrust", "eendenborst"),
    "veal": ("veau", "Kalbfleisch", "kalfsvlees"),
    # Fish
    "salmon": ("saumon", "Lachs", "zalm"),
    "tuna": ("thon", "Thunfisch", "tonijn"),
    "cod": ("morue", "Kabeljau", "kabeljauw"),
    "sea bass": ("bar", "Wolfsbarsch", "zeebaars"),
    "trout": ("truite", "Forelle", "forel"),
    "sardines": ("sardines", "Sardinen", "sardines"),
    "anchovies": ("anchois", "Sardellen", "ansjovis"),
    "mackerel": ("maquereau", "Makrele", "makreel"),
    # Seafood
    "shrimp": ("crevette", "Garnele", "garnaal"),
    "mussels": ("moules", "Muscheln", "mosselen"),
    "squid": ("calmar", "Tintenfisch", "inktvis"),
    "scallops": ("noix de Saint-Jacques", "Jakobsmuschel", "sint-jakobsschelp"),
    "crab": ("crabe", "Krabbe", "krab"),
    "clams": ("palourdes", "Venusmuscheln", "venusschelpen"),
    "octopus": ("pieuvre", "Oktopus", "octopus"),
    # Dairy
    "butter": ("beurre", "Butter", "boter"),
    "milk": ("lait", "Milch", "melk"),
    "cream": ("crème", "Sahne", "room"),
    "heavy cream": ("crème épaisse", "Schlagsahne", "slagroom"),
    "parmesan": ("parmesan", "Parmesan", "parmezaan"),
    "mozzarella": ("mozzarella", "Mozzarella", "mozzarella"),
    "cheddar": ("cheddar", "Cheddar", "cheddar"),
    "feta": ("feta", "Feta", "feta"),
    "gruyère": ("gruyère", "Gruyère", "gruyère"),
    "brie": ("brie", "Brie", "brie"),
    "yogurt": ("yaourt", "Joghurt", "yoghurt"),
    "sour cream": ("crème fraîche", "Sauerrahm", "zure room"),
    "cream cheese": ("fromage frais", "Frischkäse", "roomkaas"),
    "ricotta": ("ricotta", "Ricotta", "ricotta"),
    "gouda": ("gouda", "Gouda", "gouda"),
    # Egg
    "egg": ("œuf", "Ei", "ei"),
    # Grains
    "all-purpose flour": ("farine tout usage", "Weizenmehl", "bloem"),
    "bread flour": ("farine à pain", "Brotmehl", "broodmeel"),
    "rice": ("riz", "Reis", "rijst"),
    "spaghetti": ("spaghetti", "Spaghetti", "spaghetti"),
    "penne": ("penne", "Penne", "penne"),
    "tagliatelle": ("tagliatelles", "Tagliatelle", "tagliatelle"),
    "lasagna sheets": ("feuilles de lasagnes", "Lasagneplatten", "lasagnebladen"),
    "breadcrumbs": ("chapelure", "Paniermehl", "paneermeel"),
    "oats": ("flocons d'avoine", "Haferflocken", "havermout"),
    "couscous": ("couscous", "Couscous", "couscous"),
    "quinoa": ("quinoa", "Quinoa", "quinoa"),
    "polenta": ("polenta", "Polenta", "polenta"),
    "cornstarch": ("maïzena", "Speisestärke", "maizena"),
    "semolina": ("semoule", "Grieß", "griesmeel"),
    # Legumes
    "chickpeas": ("pois chiches", "Kichererbsen", "kikkererwten"),
    "lentils": ("lentilles", "Linsen", "linzen"),
    "black beans": ("haricots noirs", "schwarze Bohnen", "zwarte bonen"),
    "kidney beans": ("haricots rouges", "Kidneybohnen", "kidneybonen"),
    "white beans": ("haricots blancs", "weiße Bohnen", "witte bonen"),
    "tofu": ("tofu", "Tofu", "tofu"),
    "edamame": ("edamame", "Edamame", "edamame"),
    # Nuts
    "almonds": ("amandes", "Mandeln", "amandelen"),
    "walnuts": ("noix", "Walnüsse", "walnoten"),
    "cashews": ("noix de cajou", "Cashewnüsse", "cashewnoten"),
    "pine nuts": ("pignons de pin", "Pinienkerne", "pijnboompitten"),
    "hazelnuts": ("noisettes", "Haselnüsse", "hazelnoten"),
    "pecans": ("noix de pécan", "Pekannüsse", "pecannoten"),
    "pistachios": ("pistaches", "Pistazien", "pistachenoten"),
    "peanuts": ("cacahuètes", "Erdnüsse", "pinda's"),
    "sesame seeds": ("graines de sésame", "Sesamsamen", "sesamzaad"),
    # Spices
    "salt": ("sel", "Salz", "zout"),
    "black pepper": ("poivre noir", "schwarzer Pfeffer", "zwarte peper"),
    "paprika": ("paprika en poudre", "Paprikapulver", "paprikapoeder"),
    "smoked paprika": ("paprika fumé", "geräucherter Paprika", "gerookt paprikapoeder"),
    "cumin": ("cumin", "Kreuzkümmel", "komijn"),
    "coriander": ("coriandre", "Koriander", "koriander"),
    "turmeric": ("curcuma", "Kurkuma", "kurkuma"),
    "cinnamon": ("cannelle", "Zimt", "kaneel"),
    "chili flakes": ("flocons de piment", "Chiliflocken", "chilivlokken"),
    "cayenne pepper": ("poivre de Cayenne", "Cayennepfeffer", "cayennepeper"),
    "ground ginger": ("gingembre en poudre", "gemahlener Ingwer", "gemalen gember"),
    "garlic powder": ("ail en poudre", "Knoblauchpulver", "knoflookpoeder"),
    "onion powder": ("oignon en poudre", "Zwiebelpulver", "uienpoeder"),
    "nutmeg": ("noix de muscade", "Muskatnuss", "nootmuskaat"),
    "cloves": ("clous de girofle", "Nelken", "kruidnagels"),
    "cardamom": ("cardamome", "Kardamom", "kardemom"),
    "star anise": ("anis étoilé", "Sternanis", "steranijs"),
    "saffron": ("safran", "Safran", "saffraan"),
    "vanilla extract": ("extrait de vanille", "Vanilleextrakt", "vanille-extract"),
    # Herbs
    "basil": ("basilic", "Basilikum", "basilicum"),
    "oregano": ("origan", "Oregano", "oregano"),
    "thyme": ("thym", "Thymian", "tijm"),
    "rosemary": ("romarin", "Rosmarin", "rozemarijn"),
    "parsley": ("persil", "Petersilie", "peterselie"),
    "cilantro": ("coriandre frais", "Koriander frisch", "verse koriander"),
    "mint": ("menthe", "Minze", "munt"),
    "dill": ("aneth", "Dill", "dille"),
    "bay leaf": ("feuille de laurier", "Lorbeerblatt", "laurierblad"),
    "sage": ("sauge", "Salbei", "salie"),
    "tarragon": ("estragon", "Estragon", "dragon"),
    "chives": ("ciboulette", "Schnittlauch", "bieslook"),
    "lemongrass": ("citronnelle", "Zitronengras", "citroengras"),
    # Oils
    "olive oil": ("huile d'olive", "Olivenöl", "olijfolie"),
    "extra virgin olive oil": (
        "huile d'olive extra vierge",
        "natives Olivenöl extra",
        "extra vergine olijfolie",
    ),
    "vegetable oil": ("huile végétale", "Pflanzenöl", "plantaardige olie"),
    "sunflower oil": ("huile de tournesol", "Sonnenblumenöl", "zonnebloemolie"),
    "sesame oil": ("huile de sésame", "Sesamöl", "sesamolie"),
    "coconut oil": ("huile de coco", "Kokosöl", "kokosolie"),
    # Sweeteners
    "sugar": ("sucre", "Zucker", "suiker"),
    "brown sugar": ("sucre roux", "brauner Zucker", "bruine suiker"),
    "powdered sugar": ("sucre glace", "Puderzucker", "poedersuiker"),
    "honey": ("miel", "Honig", "honing"),
    "maple syrup": ("sirop d'érable", "Ahornsirup", "ahornsiroop"),
    # Condiments
    "tomato paste": ("concentré de tomate", "Tomatenmark", "tomatenpuree"),
    "tomato sauce": ("sauce tomate", "Tomatensauce", "tomatensaus"),
    "soy sauce": ("sauce soja", "Sojasoße", "sojasaus"),
    "white vinegar": ("vinaigre blanc", "weißer Essig", "witte azijn"),
    "balsamic vinegar": ("vinaigre balsamique", "Balsamicoessig", "balsamicoazijn"),
    "dijon mustard": ("moutarde de Dijon", "Dijonsenf", "dijonmosterd"),
    "ketchup": ("ketchup", "Ketchup", "ketchup"),
    "hot sauce": ("sauce piquante", "Chilisauce", "hete saus"),
    "worcestershire sauce": ("sauce Worcestershire", "Worcestershiresauce", "worcestersaus"),
    "fish sauce": ("sauce de poisson", "Fischsauce", "vissaus"),
    "coconut milk": ("lait de coco", "Kokosmilch", "kokosmelk"),
    "chicken stock": ("bouillon de poulet", "Hühnerbrühe", "kippenbouillon"),
    "beef stock": ("bouillon de bœuf", "Rinderbrühe", "runderbouillon"),
    "vegetable stock": ("bouillon de légumes", "Gemüsebrühe", "groentebouillon"),
    "mayonnaise": ("mayonnaise", "Mayonnaise", "mayonaise"),
    "tahini": ("tahini", "Tahini", "tahin"),
    "miso paste": ("pâte miso", "Misopaste", "misopasta"),
    "oyster sauce": ("sauce aux huîtres", "Austernsauce", "oestersaus"),
    "hoisin sauce": ("sauce hoisin", "Hoisinsauce", "hoisinsaus"),
    # Beverages
    "white wine": ("vin blanc", "Weißwein", "witte wijn"),
    "red wine": ("vin rouge", "Rotwein", "rode wijn"),
    "beer": ("bière", "Bier", "bier"),
    # Other
    "baking powder": ("levure chimique", "Backpulver", "bakpoeder"),
    "baking soda": ("bicarbonate de soude", "Natron", "baksoda"),
    "dry yeast": ("levure sèche", "Trockenhefe", "droge gist"),
    "dark chocolate": ("chocolat noir", "Zartbitterschokolade", "pure chocolade"),
    "cocoa powder": ("poudre de cacao", "Kakaopulver", "cacaopoeder"),
    "gelatin": ("gélatine", "Gelatine", "gelatine"),
}

LANGS = ["fr", "de", "nl"]
LANG_INDEX = {"fr": 0, "de": 1, "nl": 2}


def upgrade() -> None:
    op.create_table(
        "ingredient_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("lang", sa.String(length=5), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingredient_id", "lang"),
    )
    op.create_index("ix_ingredient_translations_name", "ingredient_translations", ["name"])

    # Look up ingredient IDs by name, then bulk-insert translations.
    conn = op.get_bind()
    rows = conn.execute(text("SELECT id, name FROM ingredients")).fetchall()
    name_to_id = {row.name: row.id for row in rows}

    to_insert = []
    for en_name, (fr_name, de_name, nl_name) in TRANSLATIONS.items():
        ing_id = name_to_id.get(en_name)
        if ing_id is None:
            continue
        for lang, translated in zip(LANGS, (fr_name, de_name, nl_name), strict=True):
            to_insert.append({"ingredient_id": ing_id, "lang": lang, "name": translated})

    if to_insert:
        conn.execute(
            text(
                "INSERT INTO ingredient_translations (ingredient_id, lang, name) "
                "VALUES (:ingredient_id, :lang, :name)"
            ),
            to_insert,
        )


def downgrade() -> None:
    op.drop_index("ix_ingredient_translations_name", table_name="ingredient_translations")
    op.drop_table("ingredient_translations")
