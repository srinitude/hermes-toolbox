# skill-plugin fixture

A minimal plugin package whose only job is to register one bundled skill
through the real Hermes plugin manager. The public export pipeline tests use
it to prove that a registered skill path must resolve to a real `SKILL.md`
file inside the package.

## Install

Copy this directory into `$HERMES_HOME/plugins/skill-plugin` inside a
temporary Hermes home and enable it with `plugins.enabled` before running
plugin discovery.
