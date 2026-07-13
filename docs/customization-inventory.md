# Customization Inventory

`inventory/public-manifest.json` is the generated source of truth for every
published artifact; this page and the README are tested against it.

Current public manifest:

- Skills: 12
- Plugin packages: 0
- Profile packages: 0
- Personality presets: 1

Where each artifact class lives:

- Public skills are tracked under `skills/<category>/<name>/`.
- Public plugin packages appear under `plugins/` only when a candidate from
  the configured public-plugin-source profile passes every publication gate;
  none currently do.
- Public profile packages appear under `profiles/` only when a native
  distribution passes every gate, including a real `hermes profile install`
  into a disposable home; none currently do.
- Personality primitives are reusable custom `/personality` presets under
  `primitives/personalities/`, each with `config.public.yaml` and
  `manifest.json`.
