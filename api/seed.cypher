// W9B recipe fixture — DO NOT MODIFY.
// Approximately 60 nodes / 115 relationships. Truncated here for the
// staging skeleton; the full seed is materialized into the live
// template at Step 9c by copying the M9 W9B fixture.

CREATE CONSTRAINT recipe_id IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE;

MERGE (sichuan:Cuisine {name: "Sichuan"});
MERGE (italian:Cuisine {name: "Italian"});

MERGE (ginger:Ingredient {name: "ginger"});
MERGE (garlic:Ingredient {name: "garlic"});

MERGE (r1:Recipe {id: "r1", name: "Mapo Tofu"})
  -[:HAS_CUISINE]->(sichuan);
MERGE (r1)-[:USES]->(ginger);
MERGE (r1)-[:USES]->(garlic);
