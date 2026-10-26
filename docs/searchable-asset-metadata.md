# Searchable asset metadata

This document defines the metadata contract for the future WordPress resource directory.
The current repository only prepares collected metadata; it does not implement the WordPress UI.

## Sound assets

- `sound_type` / `subcategory`: BGM, BGS, ME, SE, and VOICE when explicit evidence is found.
- `file_formats`: one or more explicitly identified formats: `mid`, `midi`, `ogg`, `m4a`, `mp3`, `wav`, `wma`, `flac`, `aiff`, `aif`.
- `engine_relevant=false`: do not display engine compatibility and do not exclude the sound asset when the user filters by engine.
- Do not infer file formats from the resource page URL alone. The URL may describe a web page or preview rather than the actual downloadable file.

## Graphic assets

- `subcategory`: existing detailed usage taxonomy, including character sprites, faces, battlers, tilesets, backgrounds, parallax, animation/effects, icons, UI, and title graphics; `map_object` is added for explicit map props/furniture/decorative objects.
- `graphic_style`: explicit visual style evidence, such as `pixel_art`, `illustration`, `anime`, `realistic`, `vector`, and `flat`.
- `graphic_theme`: explicit theme evidence, such as `fantasy`, `modern`, `sci_fi`, `japanese`, `horror`, `medieval`, `cyberpunk`, `nature`, and `urban`.
- `file_formats`: explicit image formats such as PNG/JPG/GIF/WebP/BMP/PSD/Aseprite where identified.
- `engine_relevant=true`: engine information may be displayed/used when known, but missing or unknown engine metadata must not exclude the item from search.

## Search behavior

- An empty list means “not identified from available evidence”; it does not mean the item lacks that feature.
- Keep facets independent: usage (`subcategory`), visual style (`graphic_style`), theme (`graphic_theme`), and file format (`file_formats`) are not interchangeable.
- Multi-value facets are supported; a pack can have more than one usage, style, theme, or format.
- Do not automatically infer compatibility from file extension. Formats offered by the material and engines supported by the user’s project are separate concepts.
- Price/license metadata remains separate and should not be used to hide paid materials by default.
