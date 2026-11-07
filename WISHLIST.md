# Wishlist

What people ask for that the cast cannot play yet. Pick anything; tell us first so two people don't make the same thing.

## From a real prompt: a night infiltration on the 1942 beach

Someone asked for a 30-second night infiltration on the 1942 beach: a swimmer comes in underwater, climbs out onto
the rocks, sneaks between the hedgehogs to cover by a bunker, crouches and talks on a radio. The set and the existing
props (`bf_hedgehog`, `bf_bunker`, `bf_barbwire`, `bf_climbnet`, `bf_barrel`, `bf_ammo_box`) already cover the beach.
The film fell short on the character and his moves, and on a facility for him to reach.

The prompt named a character from a well-known game. We make **original** people only: a new design that can play
this kind of scene, with no recognisable costume, face or gear from that game (or any other).

**Character: an infiltrator** (original design; modern or WWII-era both work)
- A diver/infiltrator in a dark wetsuit or close-fitting suit, harness and pouches, a small radio. 70–75 units tall.
- Every required and recommended clip in SPEC.md, plus these new ones:

| clip | what it shows |
|---|---|
| `swim_under` | a diver's stroke: body flat and streamlined, slow fin kick, arms along the body (the scene already places `swim` underwater, but it is a head-up surface stroke) |
| `tread` | treading water, head and shoulders up |
| `climb_out` | hands on a ledge, pulls up out of water onto the rocks, ends on one knee (in place; ends with the feet at z −24) |
| `sneak` | slow crouched walk, weight low, looking ahead |
| `cover` | crouched with the back to a wall, looking along it |
| `radio` | crouched, a hand at the ear or collar, the head bowed a little, talking |
| `look` | standing or crouched, turning the head to scan |
| `remove_fins` | sitting or kneeling, pulling a fin off each foot |

**Props**
- Diving fins, a pair (lying on the ground), for after `remove_fins`.
- Rock pieces for a rocky shore: a few boulders and a flat ledge to climb onto, 40–200 units.
- A floodlight on a pole, and a searchlight on a stand: lamp in `_glow`, with a catalog `light`.
- Chain-link fence section (about 128 wide) with razor wire on top; a gate.
- A heavy concrete or steel facility door in a frame, larger than the bunker's opening.
- Industrial silhouette pieces for the distance: a stack, a tank, a pipe run, a gantry. Simple and readable at a distance.

## Other things the cast is missing

- A diver's underwater stroke for any character: scenes already put `swim` below the surface (and film it from under the water), but it is a head-up surface stroke.
- A seated pose and a talking clip for any character (radio, briefing, a scene at a table).
- Night lamps that people carry: a torch, a lantern.
